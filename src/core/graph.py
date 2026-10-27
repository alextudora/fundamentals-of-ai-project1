import csv
from typing import List, Set

from .interfaces.graph_interface import IGraph
from .dtos.graph_dto import GraphDTO
from .dtos.edge_dto import EdgeDTO
from .dtos.node_dto import NodeDTO
from .dtos.user_profile_dto import UserProfileDTO


class GraphManager(IGraph):
    def __init__(self):
        self.graph_dto = GraphDTO()

    def add_node(self, node: NodeDTO) -> None:
        if node.id not in self.graph_dto.adjacency_list:
            self.graph_dto.adjacency_list[node.id] = []

    def add_edge(self, edge: EdgeDTO) -> None:
        if edge.source not in self.graph_dto.adjacency_list:
            self.graph_dto.adjacency_list[edge.source] = []
        self.graph_dto.adjacency_list[edge.source].append(edge)

    def get_neighbors(
            self,
            node_id: str,
            profile: UserProfileDTO,
            blocked_edges: Set[str],
    ) -> List[EdgeDTO]:
        valid_edges = []
        edges = self.graph_dto.adjacency_list.get(node_id, [])

        for edge in edges:
            if edge.edge_id in blocked_edges:
                continue

            if profile.avoid_stairs and edge.has_stairs:
                continue

            if profile.mode == "wheelchair" and not edge.wheelchair_accessible:
                continue

            if profile.covered_only and not edge.is_covered:
                continue

            valid_edges.append(edge)

        return valid_edges


def load_graph_from_csv(file_path: str) -> GraphManager:
    manager = GraphManager()
    with open(file_path, mode='r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            source = row['from'].strip()
            target = row['to'].strip()
            minutes = float(row['minutes'].strip())

            if minutes < 0:
                raise ValueError(f"Negative cost detected on edge {source}>{target}")

            edge = EdgeDTO(
                source=source,
                target=target,
                weight=minutes
            )
            manager.add_edge(edge)

            if target not in manager.graph_dto.adjacency_list:
                manager.graph_dto.adjacency_list[target] = []

    return manager

def load_nodes_from_csv(file_path: str, manager: GraphManager) -> None:
    with open(file_path, mode='r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            node_id = row['id'].strip()
            x = float(row['x'].strip())
            y = float(row['y'].strip())
            z = float(row['z'].strip()) if 'z' in row and row['z'] else 0.0

            node = NodeDTO(id=node_id, x=x, y=y, z=z)
            manager.add_node(node)
            manager.graph_dto.nodes[node_id] = node