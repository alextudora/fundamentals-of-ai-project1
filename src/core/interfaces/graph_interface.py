from abc import ABC, abstractmethod
from typing import List, Set

from ..dtos.edge_dto import EdgeDTO
from ..dtos.node_dto import NodeDTO
from ..dtos.user_profile_dto import UserProfileDTO


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
