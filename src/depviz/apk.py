"""Загрузка и разбор индекса репозитория Alpine Linux (APKINDEX).

Индекс скачивается как APKINDEX.tar.gz и разбирается вручную:
записи разделены пустой строкой, поле P — имя пакета, D — зависимости,
p — то, что пакет предоставляет (so:, cmd:, pc: и другие имена).
"""

import io
import tarfile
import urllib.error
import urllib.request

INDEX_NAME = "APKINDEX"
INDEX_ARCHIVE = "APKINDEX.tar.gz"
TIMEOUT_SECONDS = 30
CONSTRAINT_CHARS = "<>=~"
CONFLICT_PREFIX = "!"
FIELD_NAME = "P"
FIELD_DEPENDS = "D"
FIELD_PROVIDES = "p"


class RepositoryError(Exception):
    """Ошибка получения или разбора репозитория."""


def index_url(repo_url):
    """Вернуть URL архива индекса для URL репозитория."""
    if repo_url.endswith(".tar.gz"):
        return repo_url
    return repo_url.rstrip("/") + "/" + INDEX_ARCHIVE


def download(url):
    """Скачать файл по URL и вернуть его содержимое в байтах."""
    try:
        with urllib.request.urlopen(url, timeout=TIMEOUT_SECONDS) as resp:
            return resp.read()
    except (urllib.error.URLError, OSError, ValueError) as error:
        raise RepositoryError(
            f"не удалось загрузить {url}: {error}"
        ) from error


def extract_index(archive):
    """Извлечь текст файла APKINDEX из архива tar.gz."""
    try:
        with tarfile.open(fileobj=io.BytesIO(archive), mode="r:gz") as tar:
            member = tar.extractfile(INDEX_NAME)
            if member is None:
                raise KeyError(INDEX_NAME)
            return member.read().decode("utf-8")
    except (tarfile.TarError, KeyError, OSError, EOFError,
            UnicodeDecodeError) as error:
        raise RepositoryError(
            f"архив не содержит корректный {INDEX_NAME}: {error}"
        ) from error


def parse_index(text):
    """Разобрать текст APKINDEX в список записей {поле: значение}."""
    records = []
    for block in text.split("\n\n"):
        record = {}
        for line in block.splitlines():
            key, sep, value = line.partition(":")
            if sep:
                record[key] = value
        if FIELD_NAME in record:
            records.append(record)
    return records


def dependency_name(token):
    """Вернуть имя из записи зависимости без ограничения версии."""
    for index, char in enumerate(token):
        if char in CONSTRAINT_CHARS:
            return token[:index]
    return token


def build_providers(records):
    """Сопоставить каждое имя (и виртуальное) пакету, который его даёт."""
    providers = {record[FIELD_NAME]: record[FIELD_NAME] for record in records}
    for record in records:
        for token in record.get(FIELD_PROVIDES, "").split():
            providers.setdefault(dependency_name(token), record[FIELD_NAME])
    return providers


def resolve_dependencies(record, providers):
    """Вернуть имена пакетов, от которых напрямую зависит запись.

    Конфликты (!имя) пропускаются, виртуальные имена заменяются
    пакетом, который их предоставляет. Неизвестные имена остаются
    как есть: их даёт пакет из другого репозитория.
    """
    result = []
    for token in record.get(FIELD_DEPENDS, "").split():
        if token.startswith(CONFLICT_PREFIX):
            continue
        name = dependency_name(token)
        package = providers.get(name, name)
        if package != record[FIELD_NAME] and package not in result:
            result.append(package)
    return result


def build_dependency_map(records):
    """Построить словарь {пакет: список прямых зависимостей}."""
    providers = build_providers(records)
    deps = {}
    for record in records:
        deps.setdefault(
            record[FIELD_NAME], resolve_dependencies(record, providers)
        )
    return deps


def load_repository(repo_url):
    """Скачать индекс репозитория и вернуть словарь зависимостей."""
    archive = download(index_url(repo_url))
    return build_dependency_map(parse_index(extract_index(archive)))
