import csv
import os
import time
import unittest

from src.core.graph import load_graph_from_csv, load_nodes_from_csv
from src.search.ucs import UniformCostSearch
from src.search.astar import AStarSearch
from src.core.dtos.search_request_dto import SearchRequestDTO
from src.core.dtos.user_profile_dto import UserProfileDTO


class TestLargeGraphStress(unittest.TestCase):
    folder = "inputs/test_large_graph"
    edges_file = f"{folder}/edges.csv"
    nodes_file = f"{folder}/nodes.csv"
    tasks_file = f"{folder}/tasks.csv"
    grid_size = 100  # 100x100 = 10,000 noduri

    @classmethod
    def setUpClass(cls):
        """
        Generează automat fișierele CSV masive la prima rulare a suitei de teste.
        """
        os.makedirs(cls.folder, exist_ok=True)

        # Dacă fișierele nu există deja, le generăm
        if not (os.path.exists(cls.edges_file) and os.path.exists(cls.nodes_file) and os.path.exists(cls.tasks_file)):
            cls._generate_massive_csvs()

        print("\n--- RUN TASKS MASSIVE GRAPH STRESS TEST (10,000 Nodes) ---")

    @classmethod
    def _generate_massive_csvs(cls):
        print("Generating massive CSV files... This only happens once.")

        # 1. Generare nodes.csv
        with open(cls.nodes_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(["id", "x", "y"])
            for i in range(cls.grid_size):
                for j in range(cls.grid_size):
                    # Coordonate reale pentru ca A* să poată calcula distanța
                    writer.writerow([f"N_{i}_{j}", i * 10, j * 10])

        # 2. Generare edges.csv (fiecare nod e conectat cu vecinii din dreapta și de jos)
        with open(cls.edges_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(["from", "to", "minutes"])
            for i in range(cls.grid_size):
                for j in range(cls.grid_size):
                    current = f"N_{i}_{j}"
                    # Conexiune la dreapta
                    if i < cls.grid_size - 1:
                        writer.writerow([current, f"N_{i + 1}_{j}", 1.0])
                        writer.writerow([f"N_{i + 1}_{j}", current, 1.0])
                    # Conexiune în jos
                    if j < cls.grid_size - 1:
                        writer.writerow([current, f"N_{i}_{j + 1}", 1.0])
                        writer.writerow([f"N_{i}_{j + 1}", current, 1.0])

        # 3. Generare tasks.csv (din colțul stânga-sus în colțul dreapta-jos)
        with open(cls.tasks_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(["start", "goal", "blocked_edges", "required_visit"])
            writer.writerow(["N_0_0", f"N_{cls.grid_size - 1}_{cls.grid_size - 1}", "", ""])

    def setUp(self):
        # Încărcăm cele 10,000 de noduri și 40,000 de muchii
        self.graph_manager = load_graph_from_csv(self.edges_file)
        load_nodes_from_csv(self.nodes_file, self.graph_manager)
        self.graph_dto = self.graph_manager.graph_dto

        self.ucs = UniformCostSearch()
        self.astar = AStarSearch()
        self.pedestrian = UserProfileDTO(mode="pedestrian")

    def test_massive_graph_performance(self):
        """
        Testează căutarea dintr-un capăt în celălalt al grilei de 10,000 noduri.
        """
        with open(self.tasks_file, mode="r", encoding="utf-8") as f:
            tasks = list(csv.DictReader(f))
            row0 = tasks[0]
            req0 = SearchRequestDTO(start_node=row0["start"], goal_node=row0["goal"], profile=self.pedestrian)

            # Rulare Uniform Cost Search
            start_time_ucs = time.perf_counter()
            resp_ucs = self.ucs.solve(self.graph_dto, req0)
            time_ucs = (time.perf_counter() - start_time_ucs) * 1000

            # Rulare A* Search
            start_time_ast = time.perf_counter()
            resp_ast = self.astar.solve(self.graph_dto, req0)
            time_ast = (time.perf_counter() - start_time_ast) * 1000

            print(f"Stress Test: N_0_0 -> N_99_99 (Total Nodes: {len(self.graph_dto.adjacency_list)})")
            print(f"  UCS -> Cost: {resp_ucs.total_cost} | Time: {time_ucs:.2f} ms")
            print(f"  A*  -> Cost: {resp_ast.total_cost} | Time: {time_ast:.2f} ms")

            # Validări
            self.assertTrue(resp_ucs.route_found)
            self.assertTrue(resp_ast.route_found)
            self.assertEqual(resp_ucs.total_cost, resp_ast.total_cost)


if __name__ == "__main__":
    unittest.main()