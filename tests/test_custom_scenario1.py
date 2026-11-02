import csv
import os
import unittest
from src.core.graph import load_graph_from_csv, load_nodes_from_csv
from src.search.ucs import UniformCostSearch
from src.search.astar import AStarSearch
from src.core.dtos.search_request_dto import SearchRequestDTO
from src.core.dtos.user_profile_dto import UserProfileDTO


class TestCustomScenario1(unittest.TestCase):
    edges_file = "inputs/test_scenario1/edges.csv"
    nodes_file = "inputs/test_scenario1/nodes.csv"
    tasks_file = "inputs/test_scenario1/tasks.csv"

    def setUp(self):
        if not (os.path.exists(self.edges_file) and os.path.exists(self.nodes_file) and os.path.exists(
                self.tasks_file)):
            self.skipTest("CSV files from inputs/test_scenario1/ were not found.")

        self.graph_manager = load_graph_from_csv(self.edges_file)
        load_nodes_from_csv(self.nodes_file, self.graph_manager)
        self.graph_dto = self.graph_manager.graph_dto

        self.ucs = UniformCostSearch()
        self.astar = AStarSearch()
        self.profile = UserProfileDTO(mode="pedestrian")

    def test_run_all_tasks_from_csv(self):
        with open(self.tasks_file, mode="r", encoding="utf-8") as f:
            reader = list(csv.DictReader(f))
            print("\n--- RUN TASKS TEST SCENARIO 1 ---")

            # --- Task 0: S -> G (Heuristic Trap Avoidance) ---
            # Both A* and UCS must avoid node H (cost 52) and select the time-optimal route S->A->B->G (cost 12)
            row0 = reader[0]
            req0 = SearchRequestDTO(start_node=row0["start"], goal_node=row0["goal"], profile=self.profile)

            resp_ast0 = self.astar.solve(self.graph_dto, req0)
            print(f"Task 0 (Heuristic Trap): FOUND | Cost: {resp_ast0.total_cost} | Path: {' -> '.join(resp_ast0.path)}")
            self.assertTrue(resp_ast0.route_found)
            self.assertEqual(resp_ast0.path, ["S", "A", "B", "G"])
            self.assertEqual(resp_ast0.total_cost, 12.0)

            # --- Task 1: S -> G with blocked edge A>B ---
            # Blocking A>B forces a detour through R: S->A->R->B->G (cost 16)
            row1 = reader[1]
            blocked1 = set(row1["blocked_edges"].split(";"))
            req1 = SearchRequestDTO(start_node=row1["start"], goal_node=row1["goal"], blocked_edges=blocked1,
                                    profile=self.profile)

            resp_ucs1 = self.ucs.solve(self.graph_dto, req1)
            print(f"Task 1 (Blocked Edge): FOUND | Cost: {resp_ucs1.total_cost} | Path: {' -> '.join(resp_ucs1.path)}")
            self.assertTrue(resp_ucs1.route_found)
            self.assertEqual(resp_ucs1.path, ["S", "A", "R", "B", "G"])
            self.assertEqual(resp_ucs1.total_cost, 16.0)

            # --- Task 2: S -> G with mandatory visit at R ---
            # Enforces visiting node R explicitly: S->A->R->B->G (cost 16)
            row2 = reader[2]
            req2 = SearchRequestDTO(start_node=row2["start"], goal_node=row2["goal"],
                                    required_visit=row2["required_visit"], profile=self.profile)

            resp_ast2 = self.astar.solve(self.graph_dto, req2)
            print(f"Task 2 (Required Visit): FOUND | Cost: {resp_ast2.total_cost} | Path: {' -> '.join(resp_ast2.path)}")
            self.assertTrue(resp_ast2.route_found)
            self.assertEqual(resp_ast2.path, ["S", "A", "R", "B", "G"])
            self.assertEqual(resp_ast2.total_cost, 16.0)

            # --- Task 3: G -> S (Sink Node / No Outgoing Edges) ---
            # Node G has no outgoing edges. The search engine must safely return route_found=False without getting stuck
            row3 = reader[3]
            req3 = SearchRequestDTO(start_node=row3["start"], goal_node=row3["goal"], profile=self.profile)

            resp_ucs3 = self.ucs.solve(self.graph_dto, req3)
            print("Task 3 (Sink Node): No path found")
            self.assertFalse(resp_ucs3.route_found)
            self.assertEqual(resp_ucs3.path, [])


if __name__ == "__main__":
    unittest.main()