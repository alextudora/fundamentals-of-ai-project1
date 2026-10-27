import csv
import unittest
from src.core.graph import load_graph_from_csv
from src.search.ucs import UniformCostSearch
from src.core.dtos.search_request_dto import SearchRequestDTO
from src.core.dtos.user_profile_dto import UserProfileDTO


class TestIntegrationGraph1(unittest.TestCase):
    def setUp(self):
        self.graph_manager = load_graph_from_csv("inputs/graph1/edges.csv")
        self.graph_dto = self.graph_manager.graph_dto

        self.ucs = UniformCostSearch()
        self.tasks_file = "inputs/graph1/tasks.csv"

    def test_run_all_tasks_graph1(self):
        expected_results = [
            {"path": ["S", "A", "C", "G"], "cost": 7.0},
            {"path": ["S", "B", "G"], "cost": 7.0},
            {"path": ["S", "A", "C", "G"], "cost": 7.0},
            {"path": ["S", "B", "G"], "cost": 7.0},
            {"path": [], "cost": -1.0},
            {"path": [], "cost": -1.0},
            {"path": ["S", "A", "C"], "cost": 4.0},
        ]

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

                response = self.ucs.solve(self.graph_dto, request)

                if i < len(expected_results):
                    expected = expected_results[i]
                    self.assertEqual(response.path, expected["path"], f"Failed at Task {i}")
                    self.assertEqual(response.total_cost, expected["cost"], f"Failed at cost for Task {i}")

                print(f"Task {i} validated successfully. Cost={response.total_cost}, States={response.expanded_states_count}")


class TestIntegrationGraph2(unittest.TestCase):
    def setUp(self):
        # Ajustează calea către fișierele pentru graph2 (edges_2.csv / tasks_2.csv în cazul tău)
        self.graph_manager = load_graph_from_csv("inputs/graph2/edges.csv")
        self.graph_dto = self.graph_manager.graph_dto
        self.ucs = UniformCostSearch()
        self.tasks_file = "inputs/graph2/tasks.csv"

    def test_run_all_tasks_graph2(self):
        print("\n--- RUN TASKS GRAPH 2 (CAMPUS) ---")
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

                response = self.ucs.solve(self.graph_dto, request)

                if response.route_found:
                    print(f"Task {i}: FOUND | Cost: {response.total_cost} | Path: {' -> '.join(response.path)}")
                else:
                    print(f"Task {i}: No path found")


class TestIntegrationGraph3(unittest.TestCase):
    def setUp(self):
        # Asigură-te că pui calea corectă către folderul graph3 (ex: inputs/graph3/edges.csv)
        self.graph_manager = load_graph_from_csv("inputs/graph3/edges.csv")
        self.graph_dto = self.graph_manager.graph_dto
        self.ucs = UniformCostSearch()
        self.tasks_file = "inputs/graph3/tasks.csv"

    def test_run_all_tasks_graph3(self):
        print("\n--- RUN TASKS GRAPH 3 (TRAPS & MIXED EDGES) ---")
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

                response = self.ucs.solve(self.graph_dto, request)

                if response.route_found:
                    print(f"Task {i}: FOUND | Cost: {response.total_cost} | Path: {' -> '.join(response.path)}")
                else:
                    print(f"Task {i}: No path found")