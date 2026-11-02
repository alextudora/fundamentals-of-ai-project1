import csv
import os
import time
import unittest

from src.core.graph import load_graph_from_csv, load_nodes_from_csv
from src.search.ucs import UniformCostSearch
from src.search.astar import AStarSearch
from src.core.dtos.search_request_dto import SearchRequestDTO
from src.core.dtos.user_profile_dto import UserProfileDTO


class TestMediumGraph(unittest.TestCase):
    edges_file = "inputs/test_scenario4/edges.csv"
    nodes_file = "inputs/test_scenario4/nodes.csv"
    tasks_file = "inputs/test_scenario4/tasks.csv"

    @classmethod
    def setUpClass(cls):
        print("\n--- RUN TASKS MEDIUM GRAPH (30 Nodes, 15 Tasks) ---")

    def setUp(self):
        if not (os.path.exists(self.edges_file) and os.path.exists(self.nodes_file) and os.path.exists(
                self.tasks_file)):
            self.skipTest("CSV files in inputs/test_scenario4/ were not found.")

        self.graph_manager = load_graph_from_csv(self.edges_file)
        load_nodes_from_csv(self.nodes_file, self.graph_manager)
        self.graph_dto = self.graph_manager.graph_dto

        self.ucs = UniformCostSearch()
        self.astar = AStarSearch()
        self.pedestrian = UserProfileDTO(mode="pedestrian")

    def test_all_15_tasks_dynamic_consistency(self):
        """
        Runs 15 complex tasks and cross-verifies that UCS and A* always find the exact same optimal cost.
        """
        with open(self.tasks_file, mode="r", encoding="utf-8") as f:
            tasks = list(csv.DictReader(f))

            for index, row in enumerate(tasks):
                blocked = set(row["blocked_edges"].split(";")) if row["blocked_edges"] else set()
                req_visit = row["required_visit"] if row["required_visit"] else None

                req = SearchRequestDTO(
                    start_node=row["start"],
                    goal_node=row["goal"],
                    blocked_edges=blocked,
                    required_visit=req_visit,
                    profile=self.pedestrian
                )

                # Solve with UCS
                resp_ucs = self.ucs.solve(self.graph_dto, req)

                # Solve with A*
                resp_ast = self.astar.solve(self.graph_dto, req)

                # Format Output for terminal report
                status = "FOUND" if resp_ucs.route_found else "NO PATH"
                cost_str = f"Cost: {resp_ucs.total_cost}" if resp_ucs.route_found else ""
                print(f"Task {index + 1:02d} ({row['start']} -> {row['goal']}): {status} | {cost_str}")

                # Core Logic Validations: UCS and A* MUST have the same output parameters
                self.assertEqual(
                    resp_ucs.route_found,
                    resp_ast.route_found,
                    f"Mismatch on Task {index + 1}: UCS found route={resp_ucs.route_found}, A* found route={resp_ast.route_found}"
                )

                if resp_ucs.route_found:
                    self.assertEqual(
                        resp_ucs.total_cost,
                        resp_ast.total_cost,
                        f"Cost Mismatch on Task {index + 1}: UCS={resp_ucs.total_cost}, A*={resp_ast.total_cost}"
                    )


if __name__ == "__main__":
    unittest.main()