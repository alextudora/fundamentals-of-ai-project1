from dataclasses import dataclass


@dataclass(frozen=True)
class NodeDTO:
    id: str
    x: float
    y: float
    z: float = 0.0
    name: str = ""
    category: str = "general"
    is_inside_campus: bool = True

    def __post_init__(self) -> None:
        if not self.name:
            object.__setattr__(self, "name", self.id)
