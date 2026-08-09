"""Tests for the DFS pathfinder."""

from __future__ import annotations

from robot_pathfinding.algorithms.base_pathfinder import BasePathfinder
from robot_pathfinding.algorithms.bfs_pathfinder import BfsPathfinder
from robot_pathfinding.algorithms.dfs_pathfinder import DfsPathfinder
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


def test_name_is_dfs() -> None:
    assert DfsPathfinder().name() == "DFS"


def test_is_a_base_pathfinder() -> None:
    assert isinstance(DfsPathfinder(), BasePathfinder)


def test_finds_valid_path() -> None:
    obstacles = [Point(0, 1), Point(1, 1)]
    grid = Grid(4, 3, obstacles=obstacles, allow_diagonal=False)
    start, goal = Point(0, 0), Point(3, 2)

    result = DfsPathfinder().find_path(grid, start, goal)

    _assert_valid_path(result, grid, start, goal)
    assert all(point not in obstacles for point in result.path)
    assert result.execution_time_ms >= 0.0


def test_navigates_around_obstacles() -> None:
    obstacle = Point(1, 0)
    grid = Grid(3, 2, obstacles=[obstacle], allow_diagonal=False)
    start, goal = Point(0, 0), Point(2, 0)

    result = DfsPathfinder().find_path(grid, start, goal)

    _assert_valid_path(result, grid, start, goal)
    assert obstacle not in result.path


def test_no_path_returns_empty() -> None:
    blocked = [
        Point(1, 0),
        Point(2, 0),
        Point(0, 1),
        Point(1, 1),
        Point(2, 1),
        Point(0, 2),
        Point(1, 2),
    ]
    grid = Grid(3, 3, obstacles=blocked, allow_diagonal=False)
    start, goal = Point(0, 0), Point(2, 2)

    result = DfsPathfinder().find_path(grid, start, goal)

    assert not result.found
    assert result.path == []
    assert result.path_length == 0
    assert result.visited_nodes > 0


def test_start_equals_goal() -> None:
    grid = Grid(5, 5, allow_diagonal=False)
    point = Point(2, 2)

    result = DfsPathfinder().find_path(grid, point, point)

    assert result.found
    assert result.path == [point]
    assert result.path_length == 1
    assert result.visited_nodes == 1


def test_invalid_start_out_of_bounds() -> None:
    grid = Grid(5, 5, allow_diagonal=False)
    pathfinder = DfsPathfinder()

    for bad_start in (Point(-1, 0), Point(5, 0), Point(0, 5)):
        result = pathfinder.find_path(grid, bad_start, Point(4, 4))
        assert not result.found
        assert result.path == []


def test_invalid_goal_out_of_bounds() -> None:
    grid = Grid(5, 5, allow_diagonal=False)

    result = DfsPathfinder().find_path(grid, Point(0, 0), Point(5, 5))

    assert not result.found
    assert result.path == []


def test_start_on_obstacle() -> None:
    grid = Grid(5, 5, obstacles=[Point(0, 0)], allow_diagonal=False)

    result = DfsPathfinder().find_path(grid, Point(0, 0), Point(4, 4))

    assert not result.found
    assert result.path == []


def test_goal_on_obstacle() -> None:
    grid = Grid(5, 5, obstacles=[Point(4, 4)], allow_diagonal=False)

    result = DfsPathfinder().find_path(grid, Point(0, 0), Point(4, 4))

    assert not result.found
    assert result.path == []


def test_empty_grid_returns_not_found() -> None:
    grid = Grid(0, 0)
    point = Point(0, 0)

    result = DfsPathfinder().find_path(grid, point, point)

    assert not result.found
    assert result.path == []
    assert result.path_length == 0


def test_diagonal_moves_are_used() -> None:
    grid = Grid(3, 3)
    start, goal = Point(0, 0), Point(2, 2)

    result = DfsPathfinder().find_path(grid, start, goal)

    _assert_valid_diagonal_path(result, grid, start, goal)
    uses_diagonal = any(
        previous.x != current.x and previous.y != current.y
        for previous, current in zip(result.path, result.path[1:], strict=False)
    )
    assert uses_diagonal, "expected DFS to take at least one diagonal step"


def test_bfs_finds_shorter_path_than_dfs() -> None:
    grid = Grid(3, 3, allow_diagonal=False)
    start, goal = Point(0, 0), Point(0, 2)

    bfs = BfsPathfinder().find_path(grid, start, goal)
    dfs = DfsPathfinder().find_path(grid, start, goal)

    _assert_valid_path(bfs, grid, start, goal)
    _assert_valid_path(dfs, grid, start, goal)
    assert bfs.path_length == 3
    assert dfs.path_length > bfs.path_length
