import csv
import os
import unittest

from src.core.dtos import EdgeDTO
from src.core.graph import load_graph_from_csv
from src.search.ucs import UniformCostSearch
from src.search.astar import AStarSearch
from src.core.dtos.search_request_dto import SearchRequestDTO
from src.core.dtos.user_profile_dto import UserProfileDTO


class TestCustomScenario2(unittest.TestCase):
    edges_file = "inputs/test_scenario2/edges.csv"
    tasks_file = "inputs/test_scenario2/tasks.csv"

    def setUp(self):
        if not (os.path.exists(self.edges_file) and os.path.exists(self.tasks_file)):
            self.skipTest("CSV files in inputs/custom_graph/ were not found.")

        self.graph_manager = load_graph_from_csv(self.edges_file)
        self.graph_dto = self.graph_manager.graph_dto

        # Inject accessibility constraints for tests by recreating frozen EdgeDTO objects
        new_s_edges = []
        for edge in self.graph_dto.adjacency_list.get("S", []):
            if edge.target == "X":
                new_edge = EdgeDTO(
                    source="S",
                    target="X",
                    weight=2.0,
                    has_stairs=True,
                    wheelchair_accessible=False
                )
                new_s_edges.append(new_edge)
            else:
                new_s_edges.append(edge)
        self.graph_dto.adjacency_list["S"] = new_s_edges

        new_x_edges = []
        for edge in self.graph_dto.adjacency_list.get("X", []):
            if edge.target == "G":
                new_edge = EdgeDTO(
                    source="X",
                    target="G",
                    weight=2.0,
                    wheelchair_accessible=False
                )
                new_x_edges.append(new_edge)
            else:
                new_x_edges.append(edge)
        self.graph_dto.adjacency_list["X"] = new_x_edges

        self.ucs = UniformCostSearch()
        self.astar = AStarSearch()

    def test_run_all_custom_tasks_from_csv(self):
        with open(self.tasks_file, mode="r", encoding="utf-8") as f:
            tasks = list(csv.DictReader(f))
            print("\n--- RUN TASKS TEST SCENARIO 2 ---")

            # --- Task 0: Disconnected Graph and Dead Ends (S -> W) ---
            # W is completely disconnected from S (located in isolated sub-graph Z->W)
            row0 = tasks[0]
            req0 = SearchRequestDTO(
                start_node=row0["start"],
                goal_node=row0["goal"],
                profile=UserProfileDTO(mode="pedestrian")
            )

            resp_ucs0 = self.ucs.solve(self.graph_dto, req0)
            print("Task 0 (Disconnected Graph): No path found")
            self.assertFalse(resp_ucs0.route_found, "UCS should fail when searching in a disconnected graph.")

            resp_ast0 = self.astar.solve(self.graph_dto, req0)
            self.assertFalse(resp_ast0.route_found, "A* should fail when searching in a disconnected graph.")

            # --- Task 1: Graph Cycles and Mandatory Visit (S -> G with visit E & blocked S>X) ---
            # Blocking the shortcut S>X forces the path into the cycle A->E->F->A to fulfill mandatory visit E
            row1 = tasks[1]
            blocked_edges1 = set(row1["blocked_edges"].split(";"))
            req1 = SearchRequestDTO(
                start_node=row1["start"],
                goal_node=row1["goal"],
                blocked_edges=blocked_edges1,
                required_visit=row1["required_visit"],
                profile=UserProfileDTO(mode="pedestrian")
            )
            expected_path1 = ["S", "A", "E", "F", "A", "B", "G"]
            expected_cost1 = 9.0

            resp_ucs1 = self.ucs.solve(self.graph_dto, req1)
            print(f"Task 1 (Cycle & Mandatory Visit): FOUND | Cost: {resp_ucs1.total_cost} | Path: {' -> '.join(resp_ucs1.path)}")
            self.assertEqual(resp_ucs1.path, expected_path1, "UCS failed to resolve cycle with mandatory visit.")
            self.assertEqual(resp_ucs1.total_cost, expected_cost1)

            resp_ast1 = self.astar.solve(self.graph_dto, req1)
            self.assertEqual(resp_ast1.path, expected_path1, "A* failed to resolve cycle with mandatory visit.")
            self.assertEqual(resp_ast1.total_cost, expected_cost1)

            # --- Task 2: Wheelchair Accessibility Bypass (S -> G) ---
            # S->X->G (cost 4) is shorter, but edge S->X has stairs.
            # Wheelchair profile must bypass it via S->A->B->G (cost 6)
            row2 = tasks[2]
            req2 = SearchRequestDTO(
                start_node=row2["start"],
                goal_node=row2["goal"],
                profile=UserProfileDTO(mode="wheelchair")
            )

            resp_ucs2 = self.ucs.solve(self.graph_dto, req2)
            print(f"Task 2 (Wheelchair Bypass): FOUND | Cost: {resp_ucs2.total_cost} | Path: {' -> '.join(resp_ucs2.path)}")
            self.assertTrue(resp_ucs2.route_found)
            self.assertEqual(resp_ucs2.path, ["S", "A", "B", "G"])
            self.assertEqual(resp_ucs2.total_cost, 6.0)

            # --- Task 3: Wheelchair Impasse & Call Guidance Trigger (S -> X) ---
            # Target node X is only accessible via stairs. No alternative route exists.
            # Must return route_found=False and trigger call_guidance_required=True
            row3 = tasks[3]
            req3 = SearchRequestDTO(
                start_node=row3["start"],
                goal_node=row3["goal"],
                profile=UserProfileDTO(mode="wheelchair")
            )

            resp_ucs3 = self.ucs.solve(self.graph_dto, req3)
            print(f"Task 3 (Wheelchair Impasse): No path found | Call Guidance Triggered: {resp_ucs3.call_guidance_required}")
            self.assertFalse(resp_ucs3.route_found, "Wheelchair user cannot reach node X due to stairs.")
            self.assertTrue(
                resp_ucs3.call_guidance_required,
                "Call Guidance must be enabled when a wheelchair user encounters an impossible route!"
            )

if __name__ == "__main__":
    unittest.main()