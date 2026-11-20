import math

def affected_tiles(tile, neighbors):
    """受影响 tile。"""
    raise NotImplementedError("TODO: affected_tiles")

def corridor_clear(width, agent_width):
    """走廊宽度。"""
    raise NotImplementedError("TODO: corridor_clear")

def scratch_key(agent_id):
    """寻路 scratch 键。"""
    raise NotImplementedError("TODO: scratch_key")

def budget(distance, per_unit):
    """寻路预算。"""
    raise NotImplementedError("TODO: budget")

def nearest_polygon(polygons, point):
    """最近多边形。"""
    raise NotImplementedError("TODO: nearest_polygon")

def link_cost(a, b):
    """link 代价。"""
    raise NotImplementedError("TODO: link_cost")

def project_point(point, bounds):
    """投影回网格。"""
    raise NotImplementedError("TODO: project_point")

def lod_migrate(poly, new_layer):
    """LOD 迁移。"""
    raise NotImplementedError("TODO: lod_migrate")

def fallback_mesh(rebuilding, old, new):
    """重建回退。"""
    raise NotImplementedError("TODO: fallback_mesh")

def cache_version(obstacle):
    """缓存版本。"""
    raise NotImplementedError("TODO: cache_version")

def path_length(points):
    """路径长度。"""
    raise NotImplementedError("TODO: path_length")

def tile_index(position, size):
    """tile 索引。"""
    raise NotImplementedError("TODO: tile_index")

def repath_needed(old, new):
    """重寻路判定。"""
    raise NotImplementedError("TODO: repath_needed")

def nav_id(seed, index):
    """导航 id。"""
    raise NotImplementedError("TODO: nav_id")

def smooth_path(points, iterations):
    """路径平滑。"""
    raise NotImplementedError("TODO: smooth_path")
