# Copilot instructions

## Project status and architecture

This repository is an academic Fundamentals of AI project for a campus route planner. The README describes the target system: a graph-based route planner comparing Uniform Cost Search (UCS) with A*, with blocked-edge, accessibility, geofencing, and required-visit constraints. The current implementation in this branch is deliberately limited to the software-architect role: DTOs, abstract interfaces, state formulation, and an architecture decision log. Algorithm, parser, safety, UI, and testing implementations belong to other team roles.

The supplied fixtures under `inputs/` are the main domain contract for future implementation:

- Each graph directory contains an `edges.csv` file with `from,to,minutes`; edges are directed, and `minutes` is the traversal cost.
- `graph2` also contains `nodes.csv` with `id,x,y`, which can provide location coordinates for a heuristic or geofencing.
- `tasks.csv` contains `start,goal,blocked_edges,required_visit`.
- A blocked edge is encoded as `from>to`; multiple blocked edges are separated by `;`.
- Required visits are represented by node identifiers. Empty fields are valid fixture values, and some tasks intentionally reference nodes absent from the corresponding graph to exercise invalid/unreachable handling.
- The PNG files are visual references only, not runtime input.

The architecture is defined by the unified DTO package `src/core/dtos/`, the interface package `src/core/interfaces/`, and `docs/decision_log.md`. Keep graph loading, constraint handling, route validation, search algorithms, UI, and safety implementations behind these boundaries. Exchange only the DTOs between modules.

## Commands

There is no dependency manifest, build script, test suite, lint configuration, or GitHub Actions workflow at present.

There is no implemented application command yet. The current `main.py` is only the reserved integration entry point:

```powershell
python main.py
```

On Windows, the checked-in local environment can be activated with:

```powershell
.venv\Scripts\Activate.ps1
```

No test runner is configured for the architecture-only deliverable.

## Repository-specific conventions

- Use the CSV field names and constraint encodings from the fixtures as the stable external format; do not silently reinterpret `from>to` or `;` separators.
- Treat edge direction as significant. Do not automatically add reverse edges; only use directions explicitly present in `edges.csv`.
- Keep costs non-negative for UCS/A* correctness. Invalid negative-cost input should be rejected or reported explicitly, not normalized.
- Keep route validation independent from search so returned paths can be checked for valid connections, blocked edges, accessibility restrictions, required visits, and reachability.
- The README contains planned requirements and evaluation criteria. Mark functionality as implemented only after it exists in code and has been verified against representative fixture tasks.
- The search state is `(current_node, visited_required)` and is represented by `SearchStateDTO` in `src/core/dtos/search_state_dto.py`. Reaching the same node before and after the required visit represents different states.
- `NodeDTO.z` defaults to `0.0`, and an empty `NodeDTO.name` is replaced with its `id`; this is the 2D/3D compatibility contract.
- `SearchRequestDTO` and `SearchResponseDTO` are the only UI-to-engine data contract. Do not expose algorithm-specific objects across that boundary.
- Keep generated environments and IDE metadata out of changes; `.gitignore` excludes `.venv/`, `__pycache__/`, compiled Python files, `.DS_Store`, and `.idea/`.
