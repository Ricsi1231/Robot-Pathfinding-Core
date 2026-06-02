"""Result object returned by every pathfinder."""

from __future__ import annotations

from dataclasses import dataclass, field

from .point import Point


@dataclass(frozen=True, slots=True)
class PathResult:
    """Outcome of a pathfinding search.

    Attributes:
        found: Whether a path from start to goal was found.
        path: The sequence of points from start to goal inclusive; empty when
            no path was found.
        visited_nodes: Number of nodes expanded during the search.
        path_length: Number of points in ``path`` (start and goal included).
            The number of steps taken is ``path_length - 1``. ``0`` when no path
            was found.
        execution_time_ms: Wall-clock search time in milliseconds.
    """

    found: bool
    path: list[Point] = field(default_factory=list)
    visited_nodes: int = 0
    path_length: int = 0
    execution_time_ms: float = 0.0

    @classmethod
    def empty(
        cls,
        *,
        execution_time_ms: float,
        visited_nodes: int = 0,
    ) -> PathResult:
        """Build a not-found result with an empty path."""
        return cls(
            found=False,
            path=[],
            visited_nodes=visited_nodes,
            path_length=0,
            execution_time_ms=execution_time_ms,
        )
