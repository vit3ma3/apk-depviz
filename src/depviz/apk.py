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


def is_named_virtual(name):
    """Проверить, что виртуальное имя — имя пакета, а не so:, cmd: или путь.

    Такие имена (например openssh-client) становятся отдельной
    вершиной графа, зависящей от всех пакетов, которые их дают.
    """
    return ":" not in name and not name.startswith("/")


def build_providers(records):
    """Сопоставить каждому виртуальному имени список пакетов-поставщиков."""
    providers = {}
    for record in records:
        for token in record.get(FIELD_PROVIDES, "").split():
            owners = providers.setdefault(dependency_name(token), [])
            if record[FIELD_NAME] not in owners:
                owners.append(record[FIELD_NAME])
    return providers


def resolve_name(name, packages, providers):
    """Вернуть вершину графа для имени из поля D.

    Имена so:, cmd:, pc: и пути заменяются первым поставщиком.
    Настоящие пакеты, именованные виртуальные имена и неизвестные имена
    (их даёт пакет из другого репозитория) остаются как есть.
    """
    if name in packages or is_named_virtual(name):
        return name
    return providers.get(name, [name])[0]


def resolve_dependencies(record, packages, providers):
    """Вернуть имена пакетов, от которых напрямую зависит запись.

    Конфликты (!имя) и зависимость от самого себя пропускаются.
    """
    result = []
    for token in record.get(FIELD_DEPENDS, "").split():
        if token.startswith(CONFLICT_PREFIX):
            continue
        package = resolve_name(dependency_name(token), packages, providers)
        if package != record[FIELD_NAME] and package not in result:
            result.append(package)
    return result


def build_dependency_map(records):
    """Построить словарь {пакет: список прямых зависимостей}."""
    providers = build_providers(records)
    packages = {record[FIELD_NAME] for record in records}
    deps = {}
    for record in records:
        deps.setdefault(
            record[FIELD_NAME],
            resolve_dependencies(record, packages, providers),
        )
    for name, owners in providers.items():
        if is_named_virtual(name) and name not in deps:
            deps[name] = owners
    return deps


def load_repository(repo_url):
    """Скачать индекс репозитория и вернуть словарь зависимостей."""
    archive = download(index_url(repo_url))
    return build_dependency_map(parse_index(extract_index(archive)))
