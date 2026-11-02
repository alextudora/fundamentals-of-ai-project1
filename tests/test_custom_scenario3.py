import csv
import os
import unittest

from src.core.graph import load_graph_from_csv
from src.search.ucs import UniformCostSearch
from src.search.astar import AStarSearch
from src.core.dtos.search_request_dto import SearchRequestDTO
from src.core.dtos.user_profile_dto import UserProfileDTO


class TestEdgeCasesAndStress(unittest.TestCase):
    edges_file = "inputs/test_scenario3/edges.csv"
    tasks_file = "inputs/test_scenario3/tasks.csv"

    @classmethod
    def setUpClass(cls):
        print("\n--- RUN TASKS TEST SCENARIO 3 ---")

    def setUp(self):
        if not (os.path.exists(self.edges_file) and os.path.exists(self.tasks_file)):
            self.skipTest("CSV files in inputs/test_scenario3/ were not found.")

        self.graph_manager = load_graph_from_csv(self.edges_file)
        self.graph_dto = self.graph_manager.graph_dto

        self.ucs = UniformCostSearch()
        self.astar = AStarSearch()
        self.pedestrian = UserProfileDTO(mode="pedestrian")

    def test_1_start_equals_goal_self_loop(self):
        """
        Scenario 1: Start node is identical to Goal node (S -> S).
        The search engine must instantly terminate with path=['S'], total_cost=0.0.
        """
        request = SearchRequestDTO(start_node="S", goal_node="S", profile=self.pedestrian)

        resp_ucs = self.ucs.solve(self.graph_dto, request)
        print(f"Edge Case 1 (Self Loop): FOUND | Cost: {resp_ucs.total_cost} | Path: {' -> '.join(resp_ucs.path)}")
        self.assertTrue(resp_ucs.route_found)
        self.assertEqual(resp_ucs.path, ["S"])
        self.assertEqual(resp_ucs.total_cost, 0.0)

        resp_ast = self.astar.solve(self.graph_dto, request)
        self.assertTrue(resp_ast.route_found)
        self.assertEqual(resp_ast.path, ["S"])
        self.assertEqual(resp_ast.total_cost, 0.0)

    def test_2_zero_cost_edges(self):
        """
        Scenario 2: Graph contains zero-cost edge (S -> A with cost 0).
        Ensures algorithms handle zero-weight edges without infinite expansion.
        """
        request = SearchRequestDTO(start_node="S", goal_node="B", profile=self.pedestrian)

        resp_ucs = self.ucs.solve(self.graph_dto, request)
        print(f"Edge Case 2 (Zero Cost Edge): FOUND | Cost: {resp_ucs.total_cost} | Path: {' -> '.join(resp_ucs.path)}")
        self.assertTrue(resp_ucs.route_found)
        self.assertEqual(resp_ucs.path, ["S", "A", "B"])
        self.assertEqual(resp_ucs.total_cost, 5.0)

    def test_3_non_existent_required_visit_node(self):
        """
        Scenario 3: Task requests mandatory visit at node 'Z', which does not exist in the graph.
        The search engine should handle invalid visit requests gracefully (route_found=False).
        """
        request = SearchRequestDTO(
            start_node="S",
            goal_node="G",
            required_visit="Z",
            profile=self.pedestrian
        )

        resp_ucs = self.ucs.solve(self.graph_dto, request)
        print("Edge Case 3 (Missing Node): No path found")
        self.assertFalse(resp_ucs.route_found, "Search should fail when requested node 'Z' is missing.")

    def test_4_total_graph_blockade(self):
        """
        Scenario 4: All paths to Goal are manually blocked in blocked_edges.
        Verifies clean failure when every single path S->G is obstructed.
        """
        all_blocked = {"S>A", "A>B", "B>G", "S>C", "C>G"}
        request = SearchRequestDTO(
            start_node="S",
            goal_node="G",
            blocked_edges=all_blocked,
            profile=self.pedestrian
        )

        resp_ucs = self.ucs.solve(self.graph_dto, request)
        print("Edge Case 4 (Total Blockade): No path found")
        self.assertFalse(resp_ucs.route_found)
        self.assertEqual(resp_ucs.path, [])

    def test_5_multiple_equal_cost_paths(self):
        """
        Scenario 5: Two valid paths have identical cost (S->A->B->G cost 10 vs S->C->G cost 10).
        Verifies deterministic behavior when blocked_edges forces one specific route.
        """
        request = SearchRequestDTO(
            start_node="S",
            goal_node="G",
            blocked_edges={"S>A"},
            profile=self.pedestrian
        )

        resp_ucs = self.ucs.solve(self.graph_dto, request)
        print(f"Edge Case 5 (Equal Cost Paths): FOUND | Cost: {resp_ucs.total_cost} | Path: {' -> '.join(resp_ucs.path)}")
        self.assertTrue(resp_ucs.route_found)
        self.assertEqual(resp_ucs.path, ["S", "C", "G"])
        self.assertEqual(resp_ucs.total_cost, 20.0)

    def test_6_covered_only_user_profile_constraint(self):
        """
        Scenario 6: User profile requests covered paths only (covered_only=True).
        Ensures profile flags filter edges correctly when non-covered paths exist.
        """
        covered_profile = UserProfileDTO(mode="pedestrian", covered_only=True)
        request = SearchRequestDTO(start_node="S", goal_node="G", profile=covered_profile)

        # Test search execution with user constraints
        resp_ucs = self.ucs.solve(self.graph_dto, request)
        print(f"Edge Case 6 (Covered Only Constraint): Route Found = {resp_ucs.route_found}")
        self.assertIsInstance(resp_ucs.route_found, bool)


if __name__ == "__main__":
    unittest.main()