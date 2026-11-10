"""Консольный интерфейс приложения."""

import sys

from depviz.apk import RepositoryError, load_repository
from depviz.config import MODE_TEST, ConfigError, parse_config
from depviz.graph import build_graph, reverse_dependencies
from depviz.testrepo import load_test_repository

EXIT_OK = 0
EXIT_ERROR = 1


def is_known(deps, package):
    """Проверить, описан ли пакет или упомянут как зависимость."""
    if package in deps:
        return True
    return any(package in children for children in deps.values())


def load_dependencies(config):
    """Загрузить словарь зависимостей из источника по режиму работы."""
    if config.mode == MODE_TEST:
        deps = load_test_repository(config.repo)
    else:
        deps = load_repository(config.repo)
    if not is_known(deps, config.package):
        raise RepositoryError(
            f"пакет '{config.package}' не найден в репозитории"
        )
    return deps


def format_graph(graph):
    """Вернуть строки «пакет: зависимости» в порядке обхода."""
    return [f"{name}: {' '.join(deps)}".rstrip()
            for name, deps in graph.items()]


def format_reverse(deps, package):
    """Вернуть строки со списком пакетов, зависящих от package."""
    names = reverse_dependencies(deps, package)
    if not names:
        return [f"От пакета '{package}' не зависит ни один пакет"]
    return names


def main(argv=None):
    """Запустить приложение и вернуть код завершения."""
    try:
        config = parse_config(argv)
        deps = load_dependencies(config)
    except (ConfigError, RepositoryError) as error:
        print(f"Ошибка: {error}", file=sys.stderr)
        return EXIT_ERROR
    if config.reverse:
        lines = format_reverse(deps, config.package)
    else:
        lines = format_graph(build_graph(deps, config.package))
    for line in lines:
        print(line)
    return EXIT_OK
