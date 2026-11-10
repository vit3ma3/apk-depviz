"""Тесты разбора файла тестового репозитория."""

import unittest
from pathlib import Path

from depviz.apk import RepositoryError
from depviz.testrepo import load_test_repository, parse_test_repository

EXAMPLES = Path(__file__).resolve().parent.parent / "examples"


class TestRepositoryTest(unittest.TestCase):
    """Проверка формата «ИМЯ: ЗАВИСИМОСТИ»."""

    def test_parse(self):
        """Строки, комментарии и пустые строки разбираются верно."""
        text = "# граф\nA: B C\n\nB:\n"
        deps = parse_test_repository(text)
        self.assertEqual(deps, {"A": ["B", "C"], "B": []})

    def test_errors(self):
        """Неверные строки дают RepositoryError с номером строки."""
        cases = ["A B", "a: B", "A: b", "A: B\nA: C", "AB1: C"]
        for text in cases:
            with self.subTest(text=text):
                with self.assertRaisesRegex(RepositoryError, "строка"):
                    parse_test_repository(text)

    def test_examples(self):
        """Все примеры из каталога examples корректны."""
        for path in EXAMPLES.glob("*.txt"):
            with self.subTest(path=path.name):
                self.assertIn("A", load_test_repository(str(path)))


if __name__ == "__main__":
    unittest.main()
