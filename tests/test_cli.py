"""Тесты консольного интерфейса."""

import io
import unittest
from contextlib import redirect_stderr, redirect_stdout
from unittest.mock import patch

from depviz.cli import EXIT_ERROR, EXIT_OK, main

URL = "https://dl-cdn.alpinelinux.org/alpine/v3.20/main/x86_64"
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

    def test_direct_dependencies(self, _load):
        """Выводятся прямые зависимости пакета."""
        code, out, _ = run(["-p", "curl", "-r", URL])
        self.assertEqual(code, EXIT_OK)
        self.assertEqual(out.split(), ["libcurl", "musl"])

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
