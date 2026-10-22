from dataclasses import dataclass


@dataclass(frozen=True)
class EdgeDTO:
    source: str
    target: str
    weight: float
    has_stairs: bool = False
    is_covered: bool = False
    wheelchair_accessible: bool = True

    @property
    def edge_id(self) -> str:
        return f"{self.source}>{self.target}"
