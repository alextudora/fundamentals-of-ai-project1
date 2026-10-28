from dataclasses import dataclass, field
from typing import Dict, List

from .edge_dto import EdgeDTO
from .node_dto import NodeDTO


@dataclass(frozen=True)
class GraphDTO:
    adjacency_list: Dict[str, List[EdgeDTO]] = field(default_factory=dict)
    nodes: Dict[str, NodeDTO] = field(default_factory=dict)
