# Architecture decision log

## Composite search state

The algorithmic state is `(current_node, visited_required)`, not only the
current node. Two paths that reach the same node are distinct when only one
has already visited the required node. A goal state is valid only when the
goal is reached and `visited_required` is true whenever a required visit was
requested.

## Flexible coordinates

`NodeDTO` supports `x`, `y`, and optional `z`. Missing `z` is represented as
`0.0`, so the same contract supports 2D CSV files and future 3D data. Missing
`name` falls back to the node `id`.

## Module boundaries

The UI/integration layer exchanges only `SearchRequestDTO` and
`SearchResponseDTO` with `ISearchEngine`. Graph, search, UI, and safety
implementations remain replaceable behind the interfaces in
`src/core/interfaces/`.
