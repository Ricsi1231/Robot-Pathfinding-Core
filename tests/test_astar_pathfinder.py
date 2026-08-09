"""Tests for the A* pathfinder."""

from __future__ import annotations

from itertools import pairwise

from robot_pathfinding.algorithms.astar_pathfinder import AStarPathfinder
from robot_pathfinding.algorithms.base_pathfinder import BasePathfinder
from robot_pathfinding.algorithms.bfs_pathfinder import BfsPathfinder
from robot_pathfinding.models.grid import Grid
from robot_pathfinding.models.path_result import PathResult
from robot_pathfinding.models.point import Point


def _assert_valid_path(
    result: PathResult, grid: Grid, start: Point, goal: Point
) -> None:
    """Assert the path is contiguous, walkable, and spans start to goal."""
    assert result.found
    assert result.path[0] == start
    assert result.path[-1] == goal
    assert result.path_length == len(result.path)
    for point in result.path:
        assert grid.is_walkable(point)
    for previous, current in zip(result.path, result.path[1:], strict=False):
        manhattan = abs(previous.x - current.x) + abs(previous.y - current.y)
        assert manhattan == 1, f"non-adjacent step {previous} -> {current}"


def _assert_valid_diagonal_path(
    result: PathResult, grid: Grid, start: Point, goal: Point
) -> None:
    """Assert an 8-connected path is contiguous, walkable, and spans start to goal."""
    assert result.found
    assert result.path[0] == start
    assert result.path[-1] == goal
    assert result.path_length == len(result.path)
    for point in result.path:
        assert grid.is_walkable(point)
    for previous, current in zip(result.path, result.path[1:], strict=False):
        chebyshev = max(abs(previous.x - current.x), abs(previous.y - current.y))
        assert chebyshev == 1, f"non-adjacent step {previous} -> {current}"


def _path_cost(path: list[Point]) -> float:
    """Weighted length: ``sqrt(2)`` per diagonal step, ``1.0`` per cardinal step."""
    total = 0.0
    for previous, current in pairwise(path):
        diagonal = previous.x != current.x and previous.y != current.y
        total += 2**0.5 if diagonal else 1.0
    return total


def _accumulated_cost(path: list[Point], grid: Grid) -> float:
    """Total cost the planner minimises: step cost plus each entered cell's cost."""
    total = 0.0
    for previous, current in pairwise(path):
        diagonal = previous.x != current.x and previous.y != current.y
        total += (2**0.5 if diagonal else 1.0) + grid.cost(current)
    return total


def test_name_is_astar() -> None:
    assert AStarPathfinder().name() == "A*"


def test_is_a_base_pathfinder() -> None:
    assert isinstance(AStarPathfinder(), BasePathfinder)


def test_empty_grid_has_shortest_path() -> None:
    grid = Grid(10, 10, allow_diagonal=False)
    start, goal = Point(0, 0), Point(9, 9)

    result = AStarPathfinder().find_path(grid, start, goal)

    _assert_valid_path(result, grid, start, goal)
    assert result.path_length == 19
    assert result.execution_time_ms >= 0.0


def test_path_routes_around_obstacles() -> None:
    wall = [Point(2, y) for y in range(4)]
    grid = Grid(5, 5, obstacles=wall, allow_diagonal=False)
    start, goal = Point(0, 0), Point(4, 0)

    result = AStarPathfinder().find_path(grid, start, goal)

    _assert_valid_path(result, grid, start, goal)
    assert all(point not in wall for point in result.path)
    assert result.path_length == 13


def test_no_path_returns_empty() -> None:
    grid = Grid(5, 5, obstacles=[Point(3, 4), Point(4, 3)], allow_diagonal=False)
    start, goal = Point(0, 0), Point(4, 4)

    result = AStarPathfinder().find_path(grid, start, goal)

    assert not result.found
    assert result.path == []
    assert result.path_length == 0
    assert result.visited_nodes > 0


def test_start_equals_goal() -> None:
    grid = Grid(5, 5, allow_diagonal=False)
    point = Point(2, 2)

    result = AStarPathfinder().find_path(grid, point, point)

    assert result.found
    assert result.path == [point]
    assert result.path_length == 1
    assert result.visited_nodes == 1


def test_invalid_start_out_of_bounds() -> None:
    grid = Grid(5, 5, allow_diagonal=False)
    pathfinder = AStarPathfinder()

    for bad_start in (Point(-1, 0), Point(5, 0), Point(0, 5)):
        result = pathfinder.find_path(grid, bad_start, Point(4, 4))
        assert not result.found
        assert result.path == []


def test_invalid_goal_out_of_bounds() -> None:
    grid = Grid(5, 5, allow_diagonal=False)

    result = AStarPathfinder().find_path(grid, Point(0, 0), Point(5, 5))

    assert not result.found
    assert result.path == []


def test_start_on_obstacle() -> None:
    grid = Grid(5, 5, obstacles=[Point(0, 0)], allow_diagonal=False)

    result = AStarPathfinder().find_path(grid, Point(0, 0), Point(4, 4))

    assert not result.found
    assert result.path == []


def test_goal_on_obstacle() -> None:
    grid = Grid(5, 5, obstacles=[Point(4, 4)], allow_diagonal=False)

    result = AStarPathfinder().find_path(grid, Point(0, 0), Point(4, 4))

    assert not result.found
    assert result.path == []


def test_empty_grid_returns_not_found() -> None:
    grid = Grid(0, 0)
    point = Point(0, 0)

    result = AStarPathfinder().find_path(grid, point, point)

    assert not result.found
    assert result.path == []
    assert result.path_length == 0


def test_astar_matches_bfs_path_length() -> None:
    wall = [Point(2, y) for y in range(4)]
    grid = Grid(5, 5, obstacles=wall, allow_diagonal=False)
    start, goal = Point(0, 0), Point(4, 0)

    astar = AStarPathfinder().find_path(grid, start, goal)
    bfs = BfsPathfinder().find_path(grid, start, goal)

    assert astar.found and bfs.found
    assert astar.path_length == bfs.path_length


def test_astar_visits_no_more_nodes_than_bfs() -> None:
    obstacles = [Point(3, y) for y in range(7)]
    grid = Grid(10, 10, obstacles=obstacles, allow_diagonal=False)
    start, goal = Point(0, 0), Point(9, 9)

    astar = AStarPathfinder().find_path(grid, start, goal)
    bfs = BfsPathfinder().find_path(grid, start, goal)

    assert astar.found and bfs.found
    assert astar.path_length == bfs.path_length
    assert astar.visited_nodes <= bfs.visited_nodes


def test_diagonal_shortcut_is_used() -> None:
    grid = Grid(10, 10)
    start, goal = Point(0, 0), Point(9, 9)

    result = AStarPathfinder().find_path(grid, start, goal)

    _assert_valid_diagonal_path(result, grid, start, goal)
    assert result.path_length == 10


def test_diagonal_cost_not_longer_than_bfs() -> None:
    grid = Grid(10, 10)
    start, goal = Point(0, 0), Point(9, 9)

    astar = AStarPathfinder().find_path(grid, start, goal)
    bfs = BfsPathfinder().find_path(grid, start, goal)

    assert astar.found and bfs.found
    assert _path_cost(astar.path) <= _path_cost(bfs.path)
    assert _path_cost(astar.path) < 18.0


def test_corner_cutting_is_forbidden() -> None:
    grid = Grid(2, 2, obstacles=[Point(1, 0)])
    start, goal = Point(0, 0), Point(1, 1)

    result = AStarPathfinder().find_path(grid, start, goal)

    _assert_valid_diagonal_path(result, grid, start, goal)
    assert result.path_length == 3


def test_high_cost_cell_is_avoided_when_detour_is_cheaper() -> None:
    grid = Grid(3, 3, allow_diagonal=False)
    grid.set_cost(Point(1, 0), 5.0)
    start, goal = Point(0, 0), Point(2, 0)

    result = AStarPathfinder().find_path(grid, start, goal)

    _assert_valid_path(result, grid, start, goal)
    assert Point(1, 0) not in result.path
    assert result.path_length == 5


def test_costly_cell_is_traversed_when_detour_is_more_expensive() -> None:
    grid = Grid(3, 3, allow_diagonal=False)
    grid.set_cost(Point(1, 0), 1.0)
    start, goal = Point(0, 0), Point(2, 0)

    result = AStarPathfinder().find_path(grid, start, goal)

    _assert_valid_path(result, grid, start, goal)
    assert Point(1, 0) in result.path
    assert result.path_length == 3


def test_gradient_steers_to_corridor_centre() -> None:
    grid = Grid(5, 3, allow_diagonal=False)
    for x in range(5):
        grid.set_cost(Point(x, 0), 2.0)
        grid.set_cost(Point(x, 2), 2.0)
    start, goal = Point(0, 1), Point(4, 1)

    result = AStarPathfinder().find_path(grid, start, goal)

    _assert_valid_path(result, grid, start, goal)
    assert all(point.y == 1 for point in result.path)


def test_zero_cost_map_reproduces_baseline() -> None:
    grid = Grid(3, 3, allow_diagonal=False)
    start, goal = Point(0, 0), Point(2, 2)

    result = AStarPathfinder().find_path(grid, start, goal)

    _assert_valid_path(result, grid, start, goal)
    assert grid.cost(Point(1, 1)) == 0.0
    assert result.path_length == 5
