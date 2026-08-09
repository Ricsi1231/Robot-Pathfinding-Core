# Specification

The formal model and guarantees of `robot-pathfinding-core`. It complements
[architecture.md](architecture.md) (which describes *how the code is organised*) by stating
*what the library guarantees*. Where this document and the code disagree, the code and its
tests are authoritative; such a mismatch is a bug in one or the other.

## 1. Scope

The library plans paths for a point-like agent on a 2D integer grid, using four classic search
algorithms behind one interface. It is pure Python, standard-library only, with zero runtime
dependencies. It does not model kinematics, continuous space, time, or multi-agent interaction.

## 2. Coordinate and grid model

### 2.1 Points

A **`Point`** is an immutable `(x, y)` pair of integers, where `x` is the column and `y` is the
row. Points are hashable and are used as keys in the visited/came-from containers.

### 2.2 Grid dimensions

A **`Grid`** spans `x ∈ [0, width)` and `y ∈ [0, height)`.

- `width` and `height` MUST be non-negative. Negative dimensions raise `ValueError`.
- A grid is **empty** when either dimension is `0` (`Grid.is_empty` is `True`). An empty grid has
  no walkable cells, so every search over it returns a not-found result. This models a map that
  has not yet received sensor data.

### 2.3 Dynamic growth

The extent is not fixed in advance. The grid grows from the origin in the `+x` / `+y` directions
only, via `resize()`, `ensure_contains()`, and `update()`. Negative coordinates are unsupported
and raise `ValueError`. Growing the grid never removes existing obstacles or costs that remain in
bounds; shrinking (`resize()` to smaller dimensions) drops obstacles and costs now out of bounds.

### 2.4 Obstacles

Each cell is either walkable or an **obstacle**. `is_walkable(p)` is `True` iff `p` is in bounds
and not an obstacle. Obstacles are set/cleared via `add_obstacle()`, `remove_obstacle()`, the
`obstacles=` constructor argument, and `update(occupied=…, free=…)`.

### 2.5 Cost channel

Independently of the binary walkable/obstacle state, each cell carries an optional **traversal
cost** (default `0.0`), a gradient costmap layer read via `cost(p)` and set via `set_cost()`, the
`costs=` constructor argument, and `update(costs=…)`.

- A cost MUST be finite and non-negative; `NaN`, infinite, and negative values raise `ValueError`.
- Setting a cost of `0.0` clears any stored cost for that cell.
- `update(costs=…)` validates all values before applying any, so an invalid batch leaves the grid
  unmodified (all-or-nothing).
- Cost on an obstacle cell is inert — a search never enters an obstacle.

## 3. Movement model

### 3.1 Connectivity

Movement is **8-connected** by default: the four cardinal directions plus the four diagonals.
Constructing a grid with `allow_diagonal=False` restricts movement to 4-connectivity (cardinal
only). `neighbors(p)` yields the walkable cardinal neighbours first, then the permitted diagonals,
in a fixed order; every algorithm expands nodes through this single primitive.

### 3.2 No corner cutting

When diagonals are allowed, a diagonal step from a cell is forbidden if either of the two
orthogonally-adjacent cells it passes between is an obstacle. This keeps paths realistic for an
agent with physical width.

### 3.3 Step cost

For the weighted planners (A\* and Dijkstra) the cost of a single step into cell `c` is:

```
step_cost = base(move) + grid.cost(c)
base(cardinal) = 1.0
base(diagonal) = √2
```

BFS and DFS are unweighted: every step counts as `1` and the cost channel is ignored.

## 4. Algorithm guarantees

All four algorithms honour §3.1–§3.2 (connectivity and no corner cutting).

| Algorithm | Guarantee |
|-----------|-----------|
| **BFS** | Returns a path with the **fewest moves** (minimum step count). Ignores the cost channel. |
| **DFS** | Returns *a* path if one exists; **not optimal** in length or cost. Ignores the cost channel. |
| **Dijkstra** | Returns a path of **minimum total accumulated cost** (§3.3), given non-negative costs. |
| **A\*** | Same optimal result as Dijkstra, guided by an admissible heuristic (octile when diagonals are allowed, Manhattan otherwise), so it expands no more nodes than Dijkstra for the same result. |

## 5. The `BasePathfinder` contract

Every pathfinder subclasses `BasePathfinder` and implements `find_path(grid, start, goal) ->
PathResult` and `name() -> str`. `find_path` MUST:

1. **Validate inputs** — if `start` or `goal` is out of bounds or on an obstacle, return a
   not-found `PathResult` with an empty path.
2. **Handle the trivial case** — if `start == goal` and it is walkable, return a path containing
   just that point.
3. **On success** — return the reconstructed path from `start` to `goal`, inclusive of both, with
   the optimality guarantee for that algorithm (§4).
4. **On an unreachable goal** — return a not-found result with an empty path.
5. **Always populate** `visited_nodes` and `execution_time_ms`.

`find_path` reads the grid's state at call time and does not mutate the grid, so a map that
changes as sensor data arrives is handled by calling `find_path` again after each update.

## 6. `PathResult`

An immutable result returned by every search, with fields:

- `found` — whether a path was found.
- `path` — the list of points from start to goal inclusive (empty when not found).
- `visited_nodes` — number of nodes expanded during the search.
- `path_length` — number of points in `path` (the number of steps is `path_length - 1`).
- `execution_time_ms` — wall-clock search time in milliseconds.

`PathResult.empty(...)` constructs a not-found result.

## 7. Public API

`src/robot_pathfinding/__init__.py` re-exports exactly:

```text
AStarPathfinder, BasePathfinder, BfsPathfinder, DfsPathfinder,
DijkstraPathfinder, Grid, PathResult, Point
```

## 8. Known limitations

- **Non-negative coordinates only** — the grid grows from the origin; negative coordinates are
  unsupported.
- **No infinite cost** — an impassable cell is modelled as an obstacle, not as a cell with
  infinite cost.
- **Single agent, static during a search** — the grid is not modified by `find_path`; concurrent
  mutation during a search is not supported.
