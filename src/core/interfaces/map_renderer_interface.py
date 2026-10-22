from abc import ABC, abstractmethod
from typing import List

from ..dtos.edge_dto import EdgeDTO
from ..dtos.node_dto import NodeDTO
from ..dtos.search_response_dto import SearchResponseDTO


class IMapRenderer(ABC):
    """Contract between the UI and the route-planning backend."""

    @abstractmethod
    def render_map(self, nodes: List[NodeDTO], edges: List[EdgeDTO]) -> None:
        raise NotImplementedError

    @abstractmethod
    def display_route(self, response: SearchResponseDTO) -> None:
        raise NotImplementedError
