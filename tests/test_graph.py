"""Тесты построения графа зависимостей."""

import unittest

from depviz.graph import build_graph


class GraphTest(unittest.TestCase):
    """Проверка обхода в ширину."""

    def test_transitive(self):
        """В граф попадают транзитивные зависимости в порядке BFS."""
        deps = {"A": ["B", "C"], "B": ["D"], "C": ["D", "E"],
                "D": [], "E": []}
        graph = build_graph(deps, "A")
        self.assertEqual(list(graph), ["A", "B", "C", "D", "E"])
        self.assertEqual(graph["C"], ["D", "E"])

    def test_subgraph(self):
        """Недостижимые из корня пакеты не попадают в граф."""
        deps = {"A": ["B"], "B": [], "X": ["A"]}
        self.assertEqual(list(build_graph(deps, "A")), ["A", "B"])

    def test_cycle(self):
        """Цикл A -> B -> C -> A не приводит к зацикливанию."""
        deps = {"A": ["B"], "B": ["C"], "C": ["A"]}
        graph = build_graph(deps, "A")
        self.assertEqual(graph, {"A": ["B"], "B": ["C"], "C": ["A"]})

    def test_self_loop(self):
        """Пакет, зависящий от себя, обрабатывается корректно."""
        self.assertEqual(build_graph({"D": ["D"]}, "D"), {"D": ["D"]})

    def test_undescribed_leaf(self):
        """Пакет без описания — вершина без зависимостей."""
        graph = build_graph({"A": ["F"]}, "A")
        self.assertEqual(graph, {"A": ["F"], "F": []})


if __name__ == "__main__":
    unittest.main()
