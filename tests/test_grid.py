"""Tests for the Grid per-cell cost channel."""

from __future__ import annotations

import pytest

from robot_pathfinding.models.grid import Grid
from robot_pathfinding.models.point import Point


def test_cost_defaults_to_zero() -> None:
    grid = Grid(3, 3)

    assert grid.cost(Point(1, 1)) == 0.0
    assert grid.cost(Point(0, 0)) == 0.0


def test_set_cost_stores_value() -> None:
    grid = Grid(3, 3)

    grid.set_cost(Point(1, 1), 3.0)

    assert grid.cost(Point(1, 1)) == 3.0


def test_set_cost_coerces_int_to_float() -> None:
    grid = Grid(3, 3)

    grid.set_cost(Point(1, 1), 3)

    value = grid.cost(Point(1, 1))
    assert value == 3.0
    assert isinstance(value, float)


def test_set_cost_zero_is_equivalent_to_unset() -> None:
    grid = Grid(3, 3)

    grid.set_cost(Point(1, 1), 4.0)
    grid.set_cost(Point(1, 1), 0.0)

    assert grid.cost(Point(1, 1)) == 0.0


def test_set_cost_rejects_negative() -> None:
    grid = Grid(3, 3)

    with pytest.raises(ValueError):
        grid.set_cost(Point(1, 1), -1.0)


def test_set_cost_rejects_nan() -> None:
    grid = Grid(3, 3)

    with pytest.raises(ValueError):
        grid.set_cost(Point(1, 1), float("nan"))


def test_set_cost_rejects_infinity() -> None:
    grid = Grid(3, 3)

    with pytest.raises(ValueError):
        grid.set_cost(Point(1, 1), float("inf"))


def test_constructor_applies_costs() -> None:
    grid = Grid(3, 3, costs={Point(1, 1): 2.0, Point(2, 0): 5.0})

    assert grid.cost(Point(1, 1)) == 2.0
    assert grid.cost(Point(2, 0)) == 5.0
    assert grid.cost(Point(0, 0)) == 0.0


def test_update_applies_costs_and_grows_grid() -> None:
    grid = Grid(2, 2)

    grid.update(costs={Point(5, 5): 2.0})

    assert grid.width >= 6
    assert grid.height >= 6
    assert grid.cost(Point(5, 5)) == 2.0


def test_update_rejects_invalid_cost_without_mutating() -> None:
    grid = Grid(2, 2)

    with pytest.raises(ValueError):
        grid.update(occupied=[Point(1, 1)], costs={Point(0, 0): -1.0})

    assert not grid.is_obstacle(Point(1, 1))
    assert grid.cost(Point(0, 0)) == 0.0


def test_update_free_does_not_clear_cost() -> None:
    grid = Grid(3, 3)
    grid.set_cost(Point(1, 1), 4.0)

    grid.update(free=[Point(1, 1)])

    assert grid.cost(Point(1, 1)) == 4.0


def test_resize_drops_out_of_bounds_costs() -> None:
    grid = Grid(5, 5, costs={Point(4, 4): 3.0, Point(1, 1): 2.0})

    grid.resize(2, 2)

    assert grid.cost(Point(4, 4)) == 0.0
    assert grid.cost(Point(1, 1)) == 2.0


def test_zero_size_grid_is_valid_and_empty() -> None:
    grid = Grid(0, 0)

    assert grid.is_empty
    assert not grid.in_bounds(Point(0, 0))
    assert not grid.is_walkable(Point(0, 0))
    assert list(grid.neighbors(Point(0, 0))) == []


def test_single_zero_dimension_is_empty() -> None:
    assert Grid(5, 0).is_empty
    assert Grid(0, 5).is_empty
    assert not Grid(3, 3).is_empty


def test_negative_dimensions_raise() -> None:
    with pytest.raises(ValueError):
        Grid(-1, 5)
    with pytest.raises(ValueError):
        Grid(5, -1)


def test_resize_to_zero_is_allowed_and_negative_raises() -> None:
    grid = Grid(3, 3)

    grid.resize(0, 0)
    assert grid.is_empty

    with pytest.raises(ValueError):
        grid.resize(-1, 1)


def test_empty_grid_grows_from_sensor_update() -> None:
    grid = Grid(0, 0)

    grid.update(occupied=[Point(3, 3)])

    assert not grid.is_empty
    assert grid.width >= 4
    assert grid.height >= 4
    assert grid.is_obstacle(Point(3, 3))
