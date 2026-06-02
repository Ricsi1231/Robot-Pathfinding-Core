"""Tests for the BFS pathfinder and the shared grid models."""

from __future__ import annotations

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
        chebyshev = max(abs(previous.x - current.x), abs(previous.y - current.y))
        assert chebyshev == 1, f"non-adjacent step {previous} -> {current}"


def test_name_is_bfs() -> None:
    assert BfsPathfinder().name() == "BFS"


def test_is_a_base_pathfinder() -> None:
    assert isinstance(BfsPathfinder(), BasePathfinder)


def test_empty_grid_has_shortest_path() -> None:
    grid = Grid(10, 10)
    start, goal = Point(0, 0), Point(9, 9)

    result = BfsPathfinder().find_path(grid, start, goal)

    _assert_valid_path(result, grid, start, goal)
    assert result.path_length == 10
    assert 0 < result.visited_nodes <= 100
    assert result.execution_time_ms >= 0.0


def test_diagonal_moves_are_used() -> None:
    grid = Grid(3, 3)
    start, goal = Point(0, 0), Point(2, 2)

    result = BfsPathfinder().find_path(grid, start, goal)

    _assert_valid_path(result, grid, start, goal)
    assert result.path_length == 3


def test_corner_cutting_is_forbidden() -> None:
    grid = Grid(2, 2, obstacles=[Point(1, 0)])
    start, goal = Point(0, 0), Point(1, 1)

    result = BfsPathfinder().find_path(grid, start, goal)

    _assert_valid_path(result, grid, start, goal)
    assert result.path_length == 3


def test_path_routes_around_obstacles_optimally() -> None:
    grid = Grid(3, 3, obstacles=[Point(1, 1)])
    start, goal = Point(0, 0), Point(2, 2)

    result = BfsPathfinder().find_path(grid, start, goal)

    _assert_valid_path(result, grid, start, goal)
    assert Point(1, 1) not in result.path
    assert result.path_length == 5


def test_no_path_returns_empty() -> None:
    grid = Grid(5, 5, obstacles=[Point(3, 4), Point(4, 3)])
    start, goal = Point(0, 0), Point(4, 4)

    result = BfsPathfinder().find_path(grid, start, goal)

    assert not result.found
    assert result.path == []
    assert result.path_length == 0
    assert result.visited_nodes > 0


def test_start_equals_goal() -> None:
    grid = Grid(5, 5)
    point = Point(2, 2)

    result = BfsPathfinder().find_path(grid, point, point)

    assert result.found
    assert result.path == [point]
    assert result.path_length == 1
    assert result.visited_nodes == 1


def test_invalid_start_out_of_bounds() -> None:
    grid = Grid(5, 5)
    pathfinder = BfsPathfinder()

    for bad_start in (Point(-1, 0), Point(5, 0), Point(0, 5)):
        result = pathfinder.find_path(grid, bad_start, Point(4, 4))
        assert not result.found
        assert result.path == []


def test_invalid_goal_out_of_bounds() -> None:
    grid = Grid(5, 5)

    result = BfsPathfinder().find_path(grid, Point(0, 0), Point(5, 5))

    assert not result.found
    assert result.path == []


def test_start_on_obstacle() -> None:
    grid = Grid(5, 5, obstacles=[Point(0, 0)])

    result = BfsPathfinder().find_path(grid, Point(0, 0), Point(4, 4))

    assert not result.found
    assert result.path == []


def test_goal_on_obstacle() -> None:
    grid = Grid(5, 5, obstacles=[Point(4, 4)])

    result = BfsPathfinder().find_path(grid, Point(0, 0), Point(4, 4))

    assert not result.found
    assert result.path == []


def test_update_grows_grid_to_fit_sensor_data() -> None:
    grid = Grid(2, 2)

    grid.update(occupied=[Point(5, 5)])

    assert grid.width >= 6
    assert grid.height >= 6
    assert grid.is_obstacle(Point(5, 5))


def test_resize_drops_out_of_bounds_obstacles() -> None:
    grid = Grid(5, 5, obstacles=[Point(4, 4), Point(1, 1)])

    grid.resize(2, 2)

    assert not grid.is_obstacle(Point(4, 4))
    assert grid.is_obstacle(Point(1, 1))


def test_replan_after_sensor_update_blocks_corridor() -> None:
    grid = Grid(5, 1)
    start, goal = Point(0, 0), Point(4, 0)
    pathfinder = BfsPathfinder()

    before = pathfinder.find_path(grid, start, goal)
    assert before.found

    grid.update(occupied=[Point(2, 0)])
    after = pathfinder.find_path(grid, start, goal)

    assert not after.found


def test_allow_diagonal_false_yields_only_cardinals() -> None:
    grid = Grid(3, 3, allow_diagonal=False)

    neighbors = set(grid.neighbors(Point(1, 1)))

    assert neighbors == {Point(1, 0), Point(1, 2), Point(0, 1), Point(2, 1)}
