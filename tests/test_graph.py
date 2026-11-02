import os
import unittest
from src.core.graph import load_graph_from_csv
from src.core.dtos.user_profile_dto import UserProfileDTO

class TestGraphManager(unittest.TestCase):
    test_file = "test_edges_temp.csv"
    invalid_format_file = "test_invalid_format.csv"
    negative_weight_file = "test_negative_weight.csv"
    empty_file = "test_empty.csv"
    non_numeric_file = "test_non_numeric.csv"
    whitespace_file = "test_whitespace.csv"
    duplicate_edges_file = "test_duplicate.csv"
    isolated_nodes_file = "test_isolated.csv"

    def setUp(self):
        with open(self.test_file, "w", encoding="utf-8") as f:
            f.write("from,to,minutes\nS,A,2\nA,G,5\n")
        with open(self.invalid_format_file, "w", encoding="utf-8") as f:
            f.write("from,to\nS,A\nA,G\n")
        with open(self.negative_weight_file, "w", encoding="utf-8") as f:
            f.write("from,to,minutes\nS,A,-2\nA,G,5\n")
        with open(self.empty_file, "w", encoding="utf-8") as f:
            f.write("from,to,minutes\n")
        with open(self.non_numeric_file, "w", encoding="utf-8") as f:
            f.write("from,to,minutes\nS,A,invalid_cost\n")
        with open(self.whitespace_file, "w", encoding="utf-8") as f:
            f.write("from,to,minutes\n S , A ,2\nA , G ,5\n")
        with open(self.duplicate_edges_file, "w", encoding="utf-8") as f:
            f.write("from,to,minutes\nS,A,2\nS,A,4\n")
        with open(self.isolated_nodes_file, "w", encoding="utf-8") as f:
            f.write("from,to,minutes\nS,G,5\n")

    def tearDown(self):
        files_to_remove = [
            self.test_file,
            self.invalid_format_file,
            self.negative_weight_file,
            self.empty_file,
            self.non_numeric_file,
            self.whitespace_file,
            self.duplicate_edges_file,
            self.isolated_nodes_file
        ]
        for file_path in files_to_remove:
            if os.path.exists(file_path):
                os.remove(file_path)

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

    def test_load_graph_raises_exception_on_negative_weight(self):
        with self.assertRaises(ValueError):
            load_graph_from_csv(self.negative_weight_file)

    def test_load_graph_raises_exception_on_invalid_format(self):
        with self.assertRaises(KeyError):
            load_graph_from_csv(self.invalid_format_file)

    def test_load_graph_handles_empty_csv(self):
        graph = load_graph_from_csv(self.empty_file)
        self.assertEqual(len(graph.graph_dto.adjacency_list), 0)

    def test_load_graph_raises_exception_on_non_numeric_weight(self):
        with self.assertRaises(ValueError):
            load_graph_from_csv(self.non_numeric_file)

    def test_6_node_names_trimming(self):
        graph = load_graph_from_csv(self.whitespace_file)
        self.assertIn("S", graph.graph_dto.adjacency_list)
        self.assertIn("A", graph.graph_dto.adjacency_list)
        self.assertNotIn(" S ", graph.graph_dto.adjacency_list)

    def test_7_duplicate_edges(self):
        graph = load_graph_from_csv(self.duplicate_edges_file)
        edges_from_s = graph.graph_dto.adjacency_list.get("S", [])
        self.assertTrue(len(edges_from_s) >= 1)

    def test_8_isolated_nodes(self):
        graph = load_graph_from_csv(self.isolated_nodes_file)
        self.assertIn("G", graph.graph_dto.adjacency_list)
        self.assertEqual(len(graph.graph_dto.adjacency_list["G"]), 0)