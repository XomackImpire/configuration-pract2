"""Автоматические тесты основных функций проекта."""

import unittest

from src.apt_repository import get_direct_dependencies, parse_packages_index
from src.graph import build_graph, find_cycles
from src.main import load_test_repository
from src.ordering import installation_order


class AptParserTests(unittest.TestCase):
    """Проверки разбора индекса Packages."""

    def test_parse_dependencies(self):
        raw = (
            b"Package: demo\nVersion: 1.0\n"
            b"Depends: libc6 (>= 2.3), foo | bar\n\n"
            b"Package: libc6\nVersion: 2.4\n\n"
        )
        packages = parse_packages_index(raw)
        self.assertEqual(packages["demo"].dependencies, ("libc6", "foo"))
        self.assertEqual(get_direct_dependencies(packages, "demo"), ("libc6", "foo"))


class GraphTests(unittest.TestCase):
    """Проверки BFS, циклов и порядка загрузки."""

    def test_bfs_and_depth(self):
        edges = {"A": ["B", "C"], "B": ["D"], "C": ["E"], "D": [], "E": []}
        graph = build_graph("A", lambda node: edges[node], 1)
        self.assertEqual(set(graph.edges), {"A", "B", "C"})

    def test_cycle_detection(self):
        edges = {"A": ["B"], "B": ["C"], "C": ["A"]}
        graph = build_graph("A", lambda node: edges[node], 10)
        self.assertTrue(find_cycles(graph))

    def test_installation_order(self):
        edges = {"APP": ["LIB"], "LIB": ["BASE"], "BASE": []}
        graph = build_graph("APP", lambda node: edges[node], 10)
        order = installation_order(graph)
        self.assertLess(order.index("BASE"), order.index("LIB"))
        self.assertLess(order.index("LIB"), order.index("APP"))

    def test_test_repository(self):
        data = load_test_repository("data/test_repository.json")
        self.assertEqual(data["A"], ("B", "C"))


if __name__ == "__main__":
    unittest.main()
