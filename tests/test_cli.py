"""Тесты консольного интерфейса."""

import io
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path
from unittest.mock import patch

from depviz.cli import EXIT_ERROR, EXIT_OK, main

URL = "https://dl-cdn.alpinelinux.org/alpine/v3.20/main/x86_64"
EXAMPLES = Path(__file__).resolve().parent.parent / "examples"
CYCLE = str(EXAMPLES / "cycle.txt")
REPO = {"curl": ["libcurl", "musl"], "libcurl": ["musl"], "musl": []}


def run(argv):
    """Запустить main и вернуть (код, stdout, stderr)."""
    out, err = io.StringIO(), io.StringIO()
    with redirect_stdout(out), redirect_stderr(err):
        code = main(argv)
    return code, out.getvalue(), err.getvalue()


@patch("depviz.cli.load_repository", return_value=REPO)
class CliTest(unittest.TestCase):
    """Проверка вывода приложения."""

    def test_graph(self, _load):
        """Граф с транзитивными зависимостями выводится на языке D2."""
        code, out, _ = run(["-p", "curl", "-r", URL])
        self.assertEqual(code, EXIT_OK)
        self.assertEqual(out.splitlines(), [
            "direction: right",
            '"curl" -> "libcurl"',
            '"curl" -> "musl"',
            '"libcurl" -> "musl"',
            '"musl"',
        ])

    def test_test_mode(self, _load):
        """Граф строится по файлу тестового репозитория."""
        code, out, _ = run(["-p", "A", "-r", CYCLE, "-m", "test"])
        self.assertEqual(code, EXIT_OK)
        self.assertEqual(out.splitlines()[1:], [
            '"A" -> "B"', '"B" -> "C"', '"C" -> "A"', '"C" -> "D"',
            '"D" -> "D"',
        ])

    def test_reverse(self, _load):
        """--reverse выводит пакеты, зависящие от заданного."""
        code, out, _ = run(["-p", "musl", "-r", URL, "--reverse"])
        self.assertEqual(code, EXIT_OK)
        self.assertEqual(out.split(), ["curl", "libcurl"])

    def test_reverse_none(self, _load):
        """Если зависящих пакетов нет, об этом сообщается."""
        code, out, _ = run(["-p", "curl", "-r", URL, "--reverse"])
        self.assertEqual(code, EXIT_OK)
        self.assertIn("не зависит ни один пакет", out)

    def test_undescribed_package(self, _load):
        """Пакет, упомянутый только как зависимость, допустим."""
        complex_repo = str(EXAMPLES / "complex.txt")
        argv = ["-p", "F", "-r", complex_repo, "-m", "test", "--reverse"]
        code, out, _ = run(argv)
        self.assertEqual(code, EXIT_OK)
        self.assertEqual(out.split(), ["C", "A"])

    def test_unknown_package(self, _load):
        """Отсутствующий пакет — ошибка."""
        code, _, err = run(["-p", "nope", "-r", URL])
        self.assertEqual(code, EXIT_ERROR)
        self.assertIn("не найден", err)

    def test_bad_config(self, _load):
        """Ошибка параметров сообщается в stderr."""
        code, _, err = run(["-p", "curl", "-r", URL, "-m", "x"])
        self.assertEqual(code, EXIT_ERROR)
        self.assertIn("Ошибка", err)


if __name__ == "__main__":
    unittest.main()
