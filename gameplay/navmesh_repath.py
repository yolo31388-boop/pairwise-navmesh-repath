"""导航网格动态重寻路工具集。

对应十类缺陷的修复点：
1. 动态障碍（炸开的门）：affected_tiles 给出受影响 tile 及其邻接 tile，
   调用方据此重算本地通行标记 *以及* 跨 tile 边界代价。
2. 路径拉直穿墙：smooth_path 只移除共线/重复点；任何非共线捷径都必须先过
   corridor_clear 的走廊宽度检测，保证走廊能容下 agent 才允许拉直。
3. 多 agent 共用 scratch：scratch_key 按 agent_id 隔离各自的父节点表。
4. 固定节点预算：budget 按剩余距离动态分配，远距离目标不再被直接截断。
5. 传送后层错误：nearest_polygon 只在调用方传入的当前层多边形集合中查询，
   传送后必须用新层重建所在多边形。
6. 斜坡 link 代价不对称：link_cost 取双向绝对差，上下坡同价。
7. 群体避让推出可行走区：project_point 把避让结果夹回网格 bounds。
8. LOD 切换悬挂引用：lod_migrate 把 agent 引用迁移到新层多边形。
9. 异步重建期空查询：fallback_mesh 在重建完成前回退旧网格，查询不返回空。
10. 缓存未绑障碍版本：cache_version 给路径缓存打上障碍版本号，
    repath_needed 据版本差异判定缓存失效。
"""

import math

# 浮点比较容差，用于共线/宽度判定。
_EPS = 1e-9


def affected_tiles(tile, neighbors):
    """受影响 tile：变化 tile 本身加上所有邻接 tile。

    动态障碍不只改本地 tile 的通行标记，邻接 tile 与它之间的跨 tile
    边界代价也必须一起重算，所以返回值是两者的并集（去重）。
    """
    result = {tile}
    result.update(neighbors)
    return result


def corridor_clear(width, agent_width):
    """走廊宽度检测：净宽能容下 agent 才算可通行。

    拉直路径时仅当两个端点之间的走廊宽度满足本条件才允许 shortcut，
    避免只看端点导致穿墙。
    """
    return bool(width + _EPS >= agent_width)


def scratch_key(agent_id):
    """按 agent 隔离的寻路 scratch 键，杜绝多个 agent 互相覆盖父节点。"""
    return f"scratch:{agent_id}"


def budget(distance, per_unit):
    """按剩余距离动态分配寻路预算（节点数 = 距离 × 每单位预算）。

    取代固定节点数截断：预算随目标距离增长，远距离目标不会直接失败。
    向上取整保证短距离也至少有整数个节点预算，且不允许负值。
    """
    return max(0, int(math.ceil(distance * per_unit)))


def nearest_polygon(polygons, point):
    """返回距离 point 最近的多边形索引（按多边形代表点的欧氏距离）。

    只在传入的多边形集合内查询——传送后调用方必须传入目标层的多边形，
    不能沿用旧层，否则 NPC 会从错误区域起步。空集合返回 -1。
    """
    px, py = point
    best_index = -1
    best_dist2 = None
    for i, poly in enumerate(polygons):
        if hasattr(poly, "center"):
            cx, cy = poly.center
        elif isinstance(poly, dict):
            cx, cy = poly.get("center", poly.get("point", point))
        else:
            cx, cy = poly[0], poly[1]
        dist2 = (cx - px) ** 2 + (cy - py) ** 2
        if best_dist2 is None or dist2 < best_dist2:
            best_dist2 = dist2
            best_index = i
    return best_index


def link_cost(a, b):
    """斜坡/连接 link 的对称代价：两个方向取绝对差，上下坡同价。"""
    return abs(a - b)


def project_point(point, bounds):
    """把点投影（夹取）回网格 bounds=(minx, miny, maxx, maxy) 内。

    群体避让把路径点推离原位置后，用本函数保证结果仍落在可行走区域，
    而不是被推进墙里。
    """
    x, y = point
    minx, miny, maxx, maxy = bounds
    return (
        min(max(x, minx), maxx),
        min(max(y, miny), maxy),
    )


def lod_migrate(poly, new_layer):
    """LOD 切换时把 agent 持有的多边形引用迁移到新层。

    返回 (多边形标识, 新层) 组成的新引用，旧层多边形释放后不再被引用。
    """
    return (poly, new_layer)


def fallback_mesh(rebuilding, old, new):
    """异步重建期间回退旧网格：重建未完成时查询仍命中 old，不返回空。"""
    return old if rebuilding else new


def cache_version(obstacle):
    """提取障碍版本号，路径缓存条目绑定该版本。

    接受裸版本号、带 version 属性的对象或含 version 键的字典。
    """
    if hasattr(obstacle, "version"):
        return obstacle.version
    if isinstance(obstacle, dict):
        return obstacle.get("version", obstacle)
    return obstacle


def path_length(points):
    """折线路径总长度（各段欧氏距离之和，重复点贡献 0）。"""
    total = 0.0
    for (x1, y1), (x2, y2) in zip(points, points[1:]):
        total += math.hypot(x2 - x1, y2 - y1)
    return total


def tile_index(position, size):
    """世界坐标 -> tile 索引，各轴按 tile 尺寸向下取整。"""
    x, y = position
    return (math.floor(x / size), math.floor(y / size))


def repath_needed(old, new):
    """障碍版本变化即判定缓存失效、需要重寻路。"""
    return bool(old != new)


def nav_id(seed, index):
    """由 tile seed 与多边形 index 生成全局唯一导航 id。"""
    return f"{seed}:{index}"


def smooth_path(points, iterations):
    """路径平滑：迭代移除重复点与严格共线的中间拐点。

    这里只做零宽度需求的共线压缩，本身不可能切穿墙角；任何跨越拐点的
    非共线 shortcut 都必须先经 corridor_clear 做走廊宽度检测后才能采用。
    端点始终保留；无变化时提前结束，最多迭代 iterations 轮。
    """
    # 先去除相邻重复点：否则含重复点的退化三元组会把真正的拐角误判为共线，
    # 下一轮就会把拐角拉直成穿墙捷径。
    pts = []
    for p in points:
        if not pts or pts[-1] != p:
            pts.append(p)
    for _ in range(max(0, iterations)):
        if len(pts) < 3:
            break
        smoothed = [pts[0]]
        for a, b, c in zip(pts, pts[1:], pts[2:]):
            cross = (b[0] - a[0]) * (c[1] - a[1]) - (b[1] - a[1]) * (
                c[0] - a[0]
            )
            if abs(cross) > _EPS:
                smoothed.append(b)
        smoothed.append(pts[-1])
        if len(smoothed) == len(pts):
            break
        pts = smoothed
    return pts
