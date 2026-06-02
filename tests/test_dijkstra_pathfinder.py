"""Tests for the Dijkstra pathfinder."""

from __future__ import annotations

from robot_pathfinding.algorithms.astar_pathfinder import AStarPathfinder
from robot_pathfinding.algorithms.base_pathfinder import BasePathfinder
from robot_pathfinding.algorithms.bfs_pathfinder import BfsPathfinder
from robot_pathfinding.algorithms.dijkstra_pathfinder import DijkstraPathfinder
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


def test_name_is_dijkstra() -> None:
    assert DijkstraPathfinder().name() == "Dijkstra"


def test_is_a_base_pathfinder() -> None:
    assert isinstance(DijkstraPathfinder(), BasePathfinder)


def test_empty_grid_has_shortest_path() -> None:
    grid = Grid(10, 10, allow_diagonal=False)
    start, goal = Point(0, 0), Point(9, 9)

    result = DijkstraPathfinder().find_path(grid, start, goal)

    _assert_valid_path(result, grid, start, goal)
    assert result.path_length == 19  # 18 steps + start
    assert result.execution_time_ms >= 0.0


def test_path_routes_around_obstacles() -> None:
    wall = [Point(2, y) for y in range(4)]
    grid = Grid(5, 5, obstacles=wall, allow_diagonal=False)
    start, goal = Point(0, 0), Point(4, 0)

    result = DijkstraPathfinder().find_path(grid, start, goal)

    _assert_valid_path(result, grid, start, goal)
    assert all(point not in wall for point in result.path)
    assert result.path_length == 13


def test_no_path_returns_empty() -> None:
    grid = Grid(5, 5, obstacles=[Point(3, 4), Point(4, 3)], allow_diagonal=False)
    start, goal = Point(0, 0), Point(4, 4)

    result = DijkstraPathfinder().find_path(grid, start, goal)

    assert not result.found
    assert result.path == []
    assert result.path_length == 0
    assert result.visited_nodes > 0


def test_start_equals_goal() -> None:
    grid = Grid(5, 5, allow_diagonal=False)
    point = Point(2, 2)

    result = DijkstraPathfinder().find_path(grid, point, point)

    assert result.found
    assert result.path == [point]
    assert result.path_length == 1
    assert result.visited_nodes == 1


def test_invalid_start_out_of_bounds() -> None:
    grid = Grid(5, 5, allow_diagonal=False)
    pathfinder = DijkstraPathfinder()

    for bad_start in (Point(-1, 0), Point(5, 0), Point(0, 5)):
        result = pathfinder.find_path(grid, bad_start, Point(4, 4))
        assert not result.found
        assert result.path == []


def test_invalid_goal_out_of_bounds() -> None:
    grid = Grid(5, 5, allow_diagonal=False)

    result = DijkstraPathfinder().find_path(grid, Point(0, 0), Point(5, 5))

    assert not result.found
    assert result.path == []


def test_start_on_obstacle() -> None:
    grid = Grid(5, 5, obstacles=[Point(0, 0)], allow_diagonal=False)

    result = DijkstraPathfinder().find_path(grid, Point(0, 0), Point(4, 4))

    assert not result.found
    assert result.path == []


def test_goal_on_obstacle() -> None:
    grid = Grid(5, 5, obstacles=[Point(4, 4)], allow_diagonal=False)

    result = DijkstraPathfinder().find_path(grid, Point(0, 0), Point(4, 4))

    assert not result.found
    assert result.path == []


def test_dijkstra_matches_bfs_path_length() -> None:
    wall = [Point(2, y) for y in range(4)]
    grid = Grid(5, 5, obstacles=wall, allow_diagonal=False)
    start, goal = Point(0, 0), Point(4, 0)

    dijkstra = DijkstraPathfinder().find_path(grid, start, goal)
    bfs = BfsPathfinder().find_path(grid, start, goal)

    assert dijkstra.found and bfs.found
    assert dijkstra.path_length == bfs.path_length


def test_dijkstra_matches_astar_path_length() -> None:
    wall = [Point(2, y) for y in range(4)]
    grid = Grid(5, 5, obstacles=wall, allow_diagonal=False)
    start, goal = Point(0, 0), Point(4, 0)

    dijkstra = DijkstraPathfinder().find_path(grid, start, goal)
    astar = AStarPathfinder().find_path(grid, start, goal)

    assert dijkstra.found and astar.found
    assert dijkstra.path_length == astar.path_length
