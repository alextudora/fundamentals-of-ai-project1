import csv
import unittest
from src.core.graph import load_graph_from_csv, load_nodes_from_csv
from src.search.ucs import UniformCostSearch
from src.search.astar import AStarSearch
from src.core.dtos.search_request_dto import SearchRequestDTO
from src.core.dtos.user_profile_dto import UserProfileDTO


class TestIntegrationAStar(unittest.TestCase):
    def setUp(self):
        self.graph_manager = load_graph_from_csv("inputs/graph2/edges.csv")
        load_nodes_from_csv("inputs/graph2/nodes.csv", self.graph_manager)
        self.graph_dto = self.graph_manager.graph_dto

        self.ucs = UniformCostSearch()
        self.astar = AStarSearch()
        self.tasks_file = "inputs/graph2/tasks.csv"

    def test_compare_ucs_and_astar_on_graph2(self):
        print("\n" + "=" * 75)
        print("BENCHMARK REPORT: UCS vs A* (Graph: graph2_campus)")
        print("=" * 75)
        print(f"{'Task':<6} | {'Algorithm':<8} | {'Cost':<6} | {'Expanded':<9} | {'Runtime (ms)':<12}")
        print("-" * 75)

        with open(self.tasks_file, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for i, row in enumerate(reader):
                start = row["start"].strip()
                goal = row["goal"].strip()
                blocked_str = row.get("blocked_edges", "").strip()
                req_visit = row.get("required_visit", "").strip()

                req_visit = req_visit if req_visit else None
                blocked_edges = set(blocked_str.split(";")) if blocked_str else set()

                request = SearchRequestDTO(
                    start_node=start,
                    goal_node=goal,
                    required_visit=req_visit,
                    blocked_edges=blocked_edges,
                    profile=UserProfileDTO()
                )

                resp_ucs = self.ucs.solve(self.graph_dto, request)
                resp_ast = self.astar.solve(self.graph_dto, request)

                self.assertEqual(resp_ucs.path, resp_ast.path, f"Paths differ at Task {i}")
                self.assertEqual(resp_ucs.total_cost, resp_ast.total_cost, f" Costs differ at Task {i}")

                print(
                    f"Task {i:<2} | UCS      | {resp_ucs.total_cost:<6.1f} | {resp_ucs.expanded_states_count:<9} | {resp_ucs.execution_time_ms:<12.3f}")
                print(
                    f"Task {i:<2} | A* (3D)  | {resp_ast.total_cost:<6.1f} | {resp_ast.expanded_states_count:<9} | {resp_ast.execution_time_ms:<12.3f}")
                print("-" * 75)