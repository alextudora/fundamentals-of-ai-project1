from dataclasses import dataclass


@dataclass(frozen=True)
class SearchStateDTO:
    current_node: str
    visited_required: bool
