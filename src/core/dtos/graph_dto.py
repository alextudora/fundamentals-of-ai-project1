from dataclasses import dataclass, field
import sys
from pathlib import Path
from typing import Dict, List

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from src.core.dtos.edge_dto import EdgeDTO
from src.core.dtos.node_dto import NodeDTO


@dataclass(frozen=True)
class GraphDTO:
    adjacency_list: Dict[str, List[EdgeDTO]] = field(default_factory=dict)
    nodes: Dict[str, NodeDTO] = field(default_factory=dict)
