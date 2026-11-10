"""Разбор и проверка параметров командной строки."""

import argparse
import os
import re
from dataclasses import dataclass
from urllib.parse import urlparse

MODE_REAL = "real"
MODE_TEST = "test"
MODES = (MODE_REAL, MODE_TEST)
URL_SCHEMES = ("http", "https")
REAL_NAME_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._+-]*$")
TEST_NAME_RE = re.compile(r"^[A-Z]+$")


class ConfigError(Exception):
    """Ошибка в параметрах, заданных пользователем."""


@dataclass(frozen=True)
class Config:
    """Параметры запуска приложения.

    Атрибуты:
        package: имя анализируемого пакета.
        repo: URL репозитория или путь к файлу тестового репозитория.
        mode: режим работы с репозиторием: real или test.
    """

    package: str
    repo: str
    mode: str

    def items(self):
        """Вернуть параметры списком пар (ключ, значение)."""
        return [
            ("package", self.package),
            ("repo", self.repo),
            ("mode", self.mode),
        ]


def build_parser():
    """Создать разборщик опций командной строки."""
    parser = argparse.ArgumentParser(
        prog="depviz",
        description="Граф зависимостей пакетов Alpine Linux (apk).",
    )
    parser.add_argument(
        "-p", "--package", required=True,
        help="имя анализируемого пакета",
    )
    parser.add_argument(
        "-r", "--repo", required=True,
        help="URL репозитория или путь к файлу тестового репозитория",
    )
    parser.add_argument(
        "-m", "--mode", default=MODE_REAL,
        help="режим работы с репозиторием: real (по умолчанию) или test",
    )
    return parser


def validate_mode(mode):
    """Проверить режим работы и вернуть его."""
    if mode not in MODES:
        allowed = ", ".join(MODES)
        raise ConfigError(
            f"неизвестный режим '{mode}', допустимые значения: {allowed}"
        )
    return mode


def validate_package(name, mode):
    """Проверить имя пакета с учётом режима и вернуть его."""
    name = name.strip()
    if not name:
        raise ConfigError("имя пакета не может быть пустым")
    if mode == MODE_TEST and not TEST_NAME_RE.match(name):
        raise ConfigError(
            f"в тестовом режиме имя пакета — большие латинские буквы, "
            f"получено '{name}'"
        )
    if not REAL_NAME_RE.match(name):
        raise ConfigError(f"недопустимые символы в имени пакета '{name}'")
    return name


def validate_url(url):
    """Проверить, что строка — URL репозитория по http или https."""
    parsed = urlparse(url)
    if parsed.scheme not in URL_SCHEMES:
        raise ConfigError(
            f"URL репозитория должен начинаться с http:// или https://, "
            f"получено '{url}'"
        )
    if not parsed.netloc:
        raise ConfigError(f"в URL репозитория нет адреса сервера: '{url}'")
    return url


def validate_path(path):
    """Проверить, что путь указывает на читаемый файл."""
    if not os.path.exists(path):
        raise ConfigError(f"файл тестового репозитория не найден: '{path}'")
    if not os.path.isfile(path):
        raise ConfigError(f"путь к тестовому репозиторию — не файл: '{path}'")
    if not os.access(path, os.R_OK):
        raise ConfigError(f"нет прав на чтение файла: '{path}'")
    return path


def validate_repo(repo, mode):
    """Проверить источник репозитория с учётом режима."""
    repo = repo.strip()
    if not repo:
        raise ConfigError("адрес репозитория не может быть пустым")
    if mode == MODE_TEST:
        return validate_path(repo)
    return validate_url(repo)


def parse_config(argv=None):
    """Разобрать опции командной строки и вернуть проверенный Config.

    Вызывает ConfigError, если значение параметра недопустимо.
    """
    args = build_parser().parse_args(argv)
    mode = validate_mode(args.mode)
    return Config(
        package=validate_package(args.package, mode),
        repo=validate_repo(args.repo, mode),
        mode=mode,
    )
