from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..dtos.graph_dto import GraphDTO
    from ..dtos.search_request_dto import SearchRequestDTO
    from ..dtos.search_response_dto import SearchResponseDTO


class ISearchEngine(ABC):
    """Contract for UCS/A* or another interchangeable search implementation."""

    @abstractmethod
    def solve(self, graph: "GraphDTO", request: "SearchRequestDTO") -> "SearchResponseDTO":
        raise NotImplementedError
