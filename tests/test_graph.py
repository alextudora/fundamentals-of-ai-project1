import os
import unittest
from src.core.graph import load_graph_from_csv
from src.core.dtos.user_profile_dto import UserProfileDTO

class TestGraphManager(unittest.TestCase):
    test_file = "test_edges_temp.csv"

    def setUp(self):
        with open(self.test_file, "w", encoding="utf-8") as f:
            f.write("from,to,minutes\nS,A,2\nA,G,5\n")

    def tearDown(self):
        if os.path.exists(self.test_file):
            os.remove(self.test_file)

    def test_load_graph_populates_adjacency_list(self):
        graph = load_graph_from_csv(self.test_file)
        self.assertIn("S", graph.graph_dto.adjacency_list)
        self.assertIn("A", graph.graph_dto.adjacency_list)
        self.assertIn("G", graph.graph_dto.adjacency_list)
        self.assertEqual(len(graph.graph_dto.adjacency_list["S"]), 1)

    def test_get_neighbors_applies_blocked_edges(self):
        graph = load_graph_from_csv(self.test_file)
        profile = UserProfileDTO(mode="pedestrian")
        neighbors = graph.get_neighbors("S", profile, blocked_edges={"S>A"})
        self.assertEqual(len(neighbors), 0)

    def test_load_real_graph1(self):
        file_path = "inputs/graph1/edges.csv"

        if not os.path.exists(file_path):
            self.skipTest(f"Fișierul {file_path} nu a fost găsit.")

        graph = load_graph_from_csv(file_path)

        self.assertIn("S", graph.graph_dto.adjacency_list)
        self.assertIn("G", graph.graph_dto.adjacency_list)

        self.assertEqual(len(graph.graph_dto.adjacency_list["S"]), 2)