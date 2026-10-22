from dataclasses import dataclass, field
from typing import Dict, List

from .edge_dto import EdgeDTO


@dataclass(frozen=True)
class GraphDTO:
    adjacency_list: Dict[str, List[EdgeDTO]] = field(default_factory=dict)
