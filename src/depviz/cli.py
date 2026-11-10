"""Консольный интерфейс приложения."""

import sys

from depviz.apk import RepositoryError, load_repository
from depviz.config import MODE_TEST, ConfigError, parse_config

EXIT_OK = 0
EXIT_ERROR = 1


def direct_dependencies(config):
    """Загрузить репозиторий и вернуть прямые зависимости пакета."""
    if config.mode == MODE_TEST:
        raise RepositoryError("тестовый режим пока не поддерживается")
    deps = load_repository(config.repo)
    if config.package not in deps:
        raise RepositoryError(
            f"пакет '{config.package}' не найден в репозитории"
        )
    return deps[config.package]


def main(argv=None):
    """Запустить приложение и вернуть код завершения."""
    try:
        config = parse_config(argv)
        dependencies = direct_dependencies(config)
    except (ConfigError, RepositoryError) as error:
        print(f"Ошибка: {error}", file=sys.stderr)
        return EXIT_ERROR
    for name in dependencies:
        print(name)
    return EXIT_OK
