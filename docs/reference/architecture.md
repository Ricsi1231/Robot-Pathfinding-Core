# Architecture & how it works

`robot-pathfinding-core` is a small, dependency-free library organised into two packages under
`src/robot_pathfinding/`: **`models/`** (the data structures) and **`algorithms/`** (the search
implementations). The public API is re-exported from `src/robot_pathfinding/__init__.py`, which
also holds `__version__` — the single source of truth for the package version.

## Data flow

The usage pattern is the same for every algorithm:

1. Build a **`Grid`** describing the world (its size, obstacles, optional per-cell costs, and
   whether diagonal moves are allowed).
2. Construct a pathfinder (e.g. `AStarPathfinder()`).
3. Call **`find_path(grid, start, goal)`** with a start and goal **`Point`**.
4. Receive a **`PathResult`** describing whether a path was found, the path itself, and search
   metrics.

```
Point(s) ─┐
          ├─▶ Grid ──▶ Pathfinder.find_path(grid, start, goal) ──▶ PathResult
obstacles ┘
```

## Modules

### `models/`

- **`Point`** (`models/point.py`) — an immutable, frozen `dataclass` of `(x, y)` integer
  coordinates. `x` is the column (`0 .. width - 1`), `y` is the row (`0 .. height - 1`). Being
  frozen makes points hashable, so they can live in the `set`/`dict` containers used for visited
  tracking and path reconstruction.
- **`Grid`** (`models/grid.py`) — a dynamic 2D occupancy grid of walkable cells and obstacles.
  Key properties:
  - **Dynamic size**: the map is not fixed in advance. It can grow and have cells flipped
    free/occupied at runtime via `update()`, `resize()`, and `ensure_contains()`. It grows from
    the origin in the `+x` / `+y` directions only — negative coordinates are unsupported (a
    documented limitation). A grid may be **empty** (either dimension `0`, e.g. a map with no
    sensor data yet — check `grid.is_empty`): it has no walkable cells so searches return
    not-found, and it can grow from the origin as data arrives. Only negative dimensions raise.
  - **8-connected movement** by default (four cardinal directions plus four diagonals). Pass
    `allow_diagonal=False` to restrict to 4-connectivity.
  - **No corner cutting**: a diagonal step is rejected when either orthogonally-adjacent cell it
    passes is an obstacle, keeping paths realistic for a robot with physical width.
  - **Per-cell cost channel**: separate from the binary walkable/obstacle state, each cell carries
    an optional traversal cost (default `0.0`) set via `set_cost()` / `update(costs=...)` and read
    via `cost(point)`. This is a gradient costmap layer (e.g. high near obstacles, decaying with
    distance) so paths prefer clearance. Weighted planners (A\*, Dijkstra) add it to their step
    cost; BFS and DFS ignore it. Costs must be finite and non-negative.
  - `neighbors(point)` is the shared expansion primitive every search algorithm reuses: it yields
    walkable cardinal neighbours first, then the permitted diagonals.
- **`PathResult`** (`models/path_result.py`) — an immutable, frozen `dataclass` returned by every
  search. Fields: `found`, `path` (start→goal inclusive, empty when not found), `visited_nodes`
  (nodes expanded), `path_length` (points in the path; steps = `path_length - 1`), and
  `execution_time_ms`. The `PathResult.empty(...)` classmethod builds a not-found result.

### `algorithms/`

- **`BasePathfinder`** (`algorithms/base_pathfinder.py`) — the abstract base class that defines
  the contract (see below). Concrete algorithms subclass it.
- **`BfsPathfinder`**, **`DfsPathfinder`**, **`DijkstraPathfinder`**, **`AStarPathfinder`** — the
  four implementations, one per file. They differ in their search strategy but all consume a
  `Grid` and produce a `PathResult` through the same interface. All four expand neighbours through
  `Grid.neighbors`, so they honour the grid's `allow_diagonal` setting and the no-corner-cutting
  rule.

Movement and cost model, per algorithm:

- **BFS** — breadth-first; returns a minimum **move-count** path (every step costs the same). Ignores
  the per-cell cost channel.
- **DFS** — returns the first path it finds; not optimal. Ignores the per-cell cost channel.
- **Dijkstra** — returns a path minimising total accumulated cost: `1.0` per cardinal step, `√2` per
  diagonal step, plus each entered cell's `Grid.cost`.
- **A\*** — same cost model as Dijkstra, guided by an admissible heuristic (octile when diagonals are
  allowed, Manhattan otherwise), so it expands fewer nodes for the same optimal result.

## The `BasePathfinder` contract

Every pathfinder subclasses `BasePathfinder` and implements two methods:

- `find_path(grid, start, goal) -> PathResult`
- `name() -> str`

`find_path` must honour the contract documented in `base_pathfinder.py`:

- **Validate inputs** — if `start` or `goal` is out of bounds or on an obstacle, return a
  not-found `PathResult` with an empty path.
- **`start == goal`** (and walkable) — return a path containing just that point.
- **Success** — return the reconstructed path from start to goal inclusive. Cost-aware planners
  (A\*, Dijkstra) minimise the total accumulated cost (step cost plus each entered cell's
  `Grid.cost`); BFS returns a minimum move-count path and ignores the cost channel; DFS is not
  optimal.
- **Unreachable goal** — return a not-found result with an empty path.
- **Always populate** `visited_nodes` and `execution_time_ms`.

When adding a new algorithm, match this contract and add a matching test file under `tests/`
(one file per algorithm).

## Public API

`src/robot_pathfinding/__init__.py` re-exports the eight public names:

```text
AStarPathfinder, BasePathfinder, BfsPathfinder, DfsPathfinder,
DijkstraPathfinder, Grid, PathResult, Point
```

Formal requirements and guarantees will be captured separately in
[specification.md](specification.md).
