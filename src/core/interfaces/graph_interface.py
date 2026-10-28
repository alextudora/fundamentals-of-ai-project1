from abc import ABC, abstractmethod
import sys
from pathlib import Path
from typing import List, Set

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from src.core.dtos.edge_dto import EdgeDTO
from src.core.dtos.node_dto import NodeDTO
from src.core.dtos.user_profile_dto import UserProfileDTO


class IGraph(ABC):
    """Contract for the graph manager; implementation belongs to AI."""

    @abstractmethod
    def add_node(self, node: NodeDTO) -> None:
        raise NotImplementedError

    @abstractmethod
    def add_edge(self, edge: EdgeDTO) -> None:
        raise NotImplementedError

    @abstractmethod
    def get_neighbors(
        self,
        node_id: str,
        profile: UserProfileDTO,
        blocked_edges: Set[str],
    ) -> List[EdgeDTO]:
        raise NotImplementedError
