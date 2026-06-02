"""Robot-Pathfinding-Core.

Core library of robot searching and pathfinding algorithms.

This package is intentionally **dependency-free at runtime**: it relies only on
the Python standard library. Additional algorithm modules (DFS, Dijkstra, A*)
will be added here as the library grows.
"""

from __future__ import annotations

from .algorithms.base_pathfinder import BasePathfinder
from .algorithms.bfs_pathfinder import BfsPathfinder
from .models.grid import Grid
from .models.path_result import PathResult
from .models.point import Point

__version__ = "0.1.0"

__all__ = [
    "BasePathfinder",
    "BfsPathfinder",
    "Grid",
    "PathResult",
    "Point",
]
