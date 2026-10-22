from dataclasses import dataclass, field
from typing import Optional, Set

from .user_profile_dto import UserProfileDTO


@dataclass(frozen=True)
class SearchRequestDTO:
    start_node: str
    goal_node: str
    required_visit: Optional[str] = None
    blocked_edges: Set[str] = field(default_factory=set)
    profile: UserProfileDTO = field(default_factory=UserProfileDTO)
