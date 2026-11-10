"""Консольный интерфейс приложения."""

import sys

from depviz.config import ConfigError, parse_config

EXIT_OK = 0
EXIT_ERROR = 1


def main(argv=None):
    """Запустить приложение и вернуть код завершения."""
    try:
        config = parse_config(argv)
    except ConfigError as error:
        print(f"Ошибка: {error}", file=sys.stderr)
        return EXIT_ERROR
    for key, value in config.items():
        print(f"{key}={value}")
    return EXIT_OK
