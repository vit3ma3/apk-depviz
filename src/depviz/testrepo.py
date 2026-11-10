"""Файл описания тестового репозитория.

Формат: одна строка на пакет, «ИМЯ: ЗАВИСИМОСТЬ ЗАВИСИМОСТЬ ...».
Имена — большие латинские буквы. Пустые строки и строки,
начинающиеся с «#», пропускаются. Пакет, который упомянут только
как зависимость, считается пакетом без зависимостей.
"""

from depviz.apk import RepositoryError
from depviz.config import TEST_NAME_RE

COMMENT_PREFIX = "#"


def check_name(name, number):
    """Проверить имя пакета из строки с номером number."""
    if not TEST_NAME_RE.match(name):
        raise RepositoryError(
            f"строка {number}: имя пакета '{name}' должно состоять "
            f"из больших латинских букв"
        )


def parse_line(line, number):
    """Разобрать строку «ИМЯ: ЗАВИСИМОСТИ» в пару (имя, список)."""
    name, sep, rest = line.partition(":")
    if not sep:
        raise RepositoryError(
            f"строка {number}: ожидается «ИМЯ: ЗАВИСИМОСТИ», "
            f"получено '{line}'"
        )
    name = name.strip()
    children = rest.split()
    for item in [name, *children]:
        check_name(item, number)
    return name, children


def parse_test_repository(text):
    """Разобрать текст тестового репозитория в словарь зависимостей."""
    deps = {}
    for number, raw in enumerate(text.splitlines(), start=1):
        line = raw.strip()
        if not line or line.startswith(COMMENT_PREFIX):
            continue
        name, children = parse_line(line, number)
        if name in deps:
            raise RepositoryError(
                f"строка {number}: пакет '{name}' описан повторно"
            )
        deps[name] = children
    return deps


def load_test_repository(path):
    """Прочитать файл тестового репозитория и вернуть зависимости."""
    try:
        with open(path, encoding="utf-8") as handle:
            text = handle.read()
    except (OSError, UnicodeDecodeError) as error:
        raise RepositoryError(f"не удалось прочитать '{path}': {error}")
    return parse_test_repository(text)
