"""Тесты вывода графа на языке D2."""

import unittest

from depviz.d2 import DIRECTION, quote, to_d2


class D2Test(unittest.TestCase):
    """Проверка текстового представления графа."""

    def test_quote(self):
        """Имена в кавычках, спецсимволы экранируются."""
        self.assertEqual(quote("libstdc++"), '"libstdc++"')
        self.assertEqual(quote('a"b'), '"a\\"b"')

    def test_edges(self):
        """Каждое ребро — отдельная строка, листья объявляются."""
        graph = {"A": ["B", "C"], "B": ["C"], "C": []}
        self.assertEqual(to_d2(graph), [
            DIRECTION,
            '"A" -> "B"',
            '"A" -> "C"',
            '"B" -> "C"',
            '"C"',
        ])

    def test_single_node(self):
        """Граф из одной вершины без зависимостей."""
        self.assertEqual(to_d2({"A": []}), [DIRECTION, '"A"'])


if __name__ == "__main__":
    unittest.main()
