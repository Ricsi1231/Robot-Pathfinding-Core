"""2D grid coordinate."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class Point:
    """An immutable point on a 2D grid.

    ``x`` is the column index (``0 .. width - 1``) and ``y`` is the row index
    (``0 .. height - 1``). Being frozen makes instances hashable, so points can
    be stored in ``set``/``dict`` containers used for visited tracking and path
    reconstruction.
    """

    x: int
    y: int
