from abc import ABC, abstractmethod
import sys
from pathlib import Path
from typing import List

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from src.core.dtos.edge_dto import EdgeDTO
from src.core.dtos.node_dto import NodeDTO
from src.core.dtos.search_response_dto import SearchResponseDTO


class IMapRenderer(ABC):
    """Contract between the UI and the route-planning backend."""

    @abstractmethod
    def render_map(self, nodes: List[NodeDTO], edges: List[EdgeDTO]) -> None:
        raise NotImplementedError

    @abstractmethod
    def display_route(self, response: SearchResponseDTO) -> None:
        raise NotImplementedError
