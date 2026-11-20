import pytest
from gameplay import navmesh_repath as mod

CASES = [
    ("tiles", 'm.affected_tiles(1, [1, 2]) == {1, 2}'),
    ("corridor", 'm.corridor_clear(1.2, 1.0) is True'),
    ("scratch", 'm.scratch_key("a") == "scratch:a"'),
    ("budget", 'm.budget(10, 2) == 20'),
    ("nearest", 'm.nearest_polygon([(0, 0), (3, 4)], (0, 0)) == 0'),
    ("link", 'm.link_cost(2, 5) == 3'),
    ("project", 'm.project_point((5, 5), (0, 0, 10, 10)) == (5, 5)'),
    ("project2", 'm.project_point((-1, 12), (0, 0, 10, 10)) == (0, 10)'),
    ("migrate", 'm.lod_migrate("p1", 2) == ("p1", 2)'),
    ("fallback", 'm.fallback_mesh(True, "old", "new") == "old"'),
    ("version", 'm.cache_version(7) == 7'),
    ("length", 'm.path_length([(0, 0), (3, 4), (3, 4)]) == approx(5.0)'),
    ("tile", 'm.tile_index((4, 7), 4) == (1, 1)'),
    ("repath", 'm.repath_needed(1, 2) is True'),
    ("id", 'm.nav_id(3, 2) == "3:2"')
]

@pytest.mark.parametrize("name,expr", CASES, ids=[c[0] for c in CASES])
def test_contract(name, expr):
    assert eval(expr, {"m": mod, "approx": pytest.approx})
