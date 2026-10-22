from dataclasses import dataclass


@dataclass(frozen=True)
class UserProfileDTO:
    mode: str = "pedestrian"
    avoid_stairs: bool = False
    covered_only: bool = False
