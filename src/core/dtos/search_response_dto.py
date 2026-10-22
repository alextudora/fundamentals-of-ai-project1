from dataclasses import dataclass
from typing import List


@dataclass(frozen=True)
class SearchResponseDTO:
    path: List[str]
    total_cost: float
    expanded_states_count: int
    execution_time_ms: float
    route_found: bool
    call_guidance_required: bool = False
