from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..dtos.graph_dto import GraphDTO
    from ..dtos.search_request_dto import SearchRequestDTO


class ISafetyGuard(ABC):
    """Contract for request validation owned by the safety role."""

    @abstractmethod
    def validate_request(self, request: "SearchRequestDTO", graph: "GraphDTO") -> bool:
        raise NotImplementedError
