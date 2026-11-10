"""Консольный интерфейс приложения."""

import sys

from depviz.apk import RepositoryError, load_repository
from depviz.config import MODE_TEST, ConfigError, parse_config
from depviz.graph import build_graph
from depviz.testrepo import load_test_repository

EXIT_OK = 0
EXIT_ERROR = 1


def load_dependencies(config):
    """Загрузить словарь зависимостей из источника по режиму работы."""
    if config.mode == MODE_TEST:
        deps = load_test_repository(config.repo)
    else:
        deps = load_repository(config.repo)
    if config.package not in deps:
        raise RepositoryError(
            f"пакет '{config.package}' не найден в репозитории"
        )
    return deps


def format_graph(graph):
    """Вернуть строки «пакет: зависимости» в порядке обхода."""
    return [f"{name}: {' '.join(deps)}".rstrip()
            for name, deps in graph.items()]


def main(argv=None):
    """Запустить приложение и вернуть код завершения."""
    try:
        config = parse_config(argv)
        deps = load_dependencies(config)
    except (ConfigError, RepositoryError) as error:
        print(f"Ошибка: {error}", file=sys.stderr)
        return EXIT_ERROR
    for line in format_graph(build_graph(deps, config.package)):
        print(line)
    return EXIT_OK
