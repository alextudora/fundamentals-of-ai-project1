from dataclasses import dataclass, field
import sys
from pathlib import Path
from typing import Optional, Set

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from src.core.dtos.user_profile_dto import UserProfileDTO


@dataclass(frozen=True)
class SearchRequestDTO:
    start_node: str
    goal_node: str
    required_visit: Optional[str] = None
    blocked_edges: Set[str] = field(default_factory=set)
    profile: UserProfileDTO = field(default_factory=UserProfileDTO)
