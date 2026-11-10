"""Тесты разбора и проверки параметров."""

import io
import os
import tempfile
import unittest
from contextlib import redirect_stderr

from depviz.config import ConfigError, parse_config

URL = "https://dl-cdn.alpinelinux.org/alpine/v3.20/main/x86_64"


class ConfigTest(unittest.TestCase):
    """Проверка опций командной строки."""

    def setUp(self):
        """Создать временный файл тестового репозитория."""
        handle, self.path = tempfile.mkstemp()
        os.close(handle)

    def tearDown(self):
        """Удалить временный файл."""
        os.remove(self.path)

    def test_real_mode(self):
        """Корректные параметры реального режима."""
        config = parse_config(["-p", "curl", "-r", URL])
        self.assertEqual(config.package, "curl")
        self.assertEqual(config.mode, "real")

    def test_test_mode(self):
        """Корректные параметры тестового режима."""
        config = parse_config(["-p", "A", "-r", self.path, "-m", "test"])
        self.assertEqual(config.repo, self.path)

    def test_errors(self):
        """Каждый неверный параметр даёт ConfigError."""
        cases = [
            ["-p", " ", "-r", URL],
            ["-p", "bad name", "-r", URL],
            ["-p", "a", "-r", self.path, "-m", "test"],
            ["-p", "curl", "-r", "ftp://host/repo"],
            ["-p", "curl", "-r", "https://"],
            ["-p", "curl", "-r", ""],
            ["-p", "A", "-r", "/no/such/file", "-m", "test"],
            ["-p", "A", "-r", tempfile.gettempdir(), "-m", "test"],
            ["-p", "curl", "-r", URL, "-m", "fast"],
        ]
        for argv in cases:
            with self.subTest(argv=argv):
                with self.assertRaises(ConfigError):
                    parse_config(argv)

    def test_missing_option(self):
        """Без обязательной опции argparse завершает работу."""
        with redirect_stderr(io.StringIO()):
            with self.assertRaises(SystemExit):
                parse_config(["-p", "curl"])


if __name__ == "__main__":
    unittest.main()
