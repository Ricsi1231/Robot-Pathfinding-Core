# Robot Pathfinding Core

[![pipeline status](https://gitlab.com/robot-pathfinding-ros2-platfrom/robot-pathfinding-core/badges/dev/pipeline.svg)](https://gitlab.com/robot-pathfinding-ros2-platfrom/robot-pathfinding-core/-/pipelines)
[![CI](https://github.com/robot-pathfinding-ros2-platform/robot-pathfinding-core/actions/workflows/ci.yml/badge.svg?branch=dev)](https://github.com/robot-pathfinding-ros2-platform/robot-pathfinding-core/actions/workflows/ci.yml)

Core library of robot searching and pathfinding algorithms — **pure Python standard library,
zero runtime dependencies**.

It models a 2D occupancy grid that a robot builds up from sensor data and finds paths across it
using a family of classic search algorithms behind one common interface. The grid is dynamic
(it can start empty and grow, and have cells flipped free/occupied at runtime) and 8-connected by default, with
corner-cutting disallowed so paths stay realistic for a robot with physical width. Beyond binary
obstacles, cells carry an optional per-cell **cost** (a gradient costmap layer) so paths can
prefer clearance — the weighted planners (A\* and Dijkstra) honour it; BFS and DFS do not.

## Algorithms

| Class | Algorithm |
|-------|-----------|
| `BfsPathfinder` | Breadth-first search |
| `DfsPathfinder` | Depth-first search |
| `DijkstraPathfinder` | Dijkstra's algorithm |
| `AStarPathfinder` | A\* search |

All pathfinders share the `BasePathfinder` interface and operate on a `Grid` of `Point`s,
returning a `PathResult`. They all honour the grid's `allow_diagonal` setting (no corner cutting).
The weighted planners — A\* and Dijkstra — cost a cardinal step `1.0`, a diagonal step `√2`, and add
each cell's optional per-cell cost, so they return true shortest paths and can follow a gradient
costmap; BFS (minimum move-count) and DFS ignore the cost channel.

## Quick start

```python
from robot_pathfinding import AStarPathfinder, Grid, Point

grid = Grid(width=10, height=10, obstacles=[Point(3, 3), Point(3, 4), Point(3, 5)])

# Optional: bias A*/Dijkstra away from cells near the wall (a gradient costmap).
grid.set_cost(Point(2, 4), 5.0)

result = AStarPathfinder().find_path(grid, start=Point(0, 0), goal=Point(9, 9))

if result.found:
    print(f"path of {result.path_length} steps, visited {result.visited_nodes} nodes")
    print(result.path)
```

## Documentation

- **[Build & run](docs/guides/building.md)** — requirements, installation, running it, the
  development workflow, and CI/CD.
- **[Using this library in another project](docs/guides/consuming.md)** — installing released
  versions from the GitLab PyPI Package Registry.
- **[Architecture & how it works](docs/reference/architecture.md)** — the modules, the data flow,
  and the `BasePathfinder` contract.
- **[Development guidelines](docs/reference/development-guidelines.md)** — branching, tasks, and
  daily workflow for contributors.
- **[Specification](docs/reference/specification.md)** — formal specification: the grid and
  movement model, algorithm guarantees, and the `BasePathfinder` / `PathResult` contracts.

## License

[MIT](LICENSE)
