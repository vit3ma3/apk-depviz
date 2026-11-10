"""Тесты разбора индекса репозитория Alpine Linux."""

import io
import os
import tarfile
import tempfile
import unittest
from pathlib import Path

from depviz.apk import (
    RepositoryError,
    build_dependency_map,
    dependency_name,
    extract_index,
    index_url,
    load_repository,
    parse_index,
)

INDEX = """C:Q1abc=
P:curl
V:8.14.1-r2
D:libcurl=8.14.1-r2 so:libc.musl-x86_64.so.1 so:libz.so.1 !curl-old
p:cmd:curl=8.14.1-r2

P:libcurl
V:8.14.1-r2
D:so:libc.musl-x86_64.so.1 so:libz.so.1 ca-certificates-bundle
p:so:libcurl.so.4=4.8.0

P:musl
V:1.2.5-r1
p:so:libc.musl-x86_64.so.1=1

P:zlib
V:1.3.1-r1
D:so:libc.musl-x86_64.so.1 zlib>=1.0
p:so:libz.so.1=1.3.1

P:ssh-default
D:so:libz.so.1 !ssh-krb5
p:ssh-client=1 cmd:ssh=1

P:ssh-krb5
D:so:libz.so.1 !ssh-default
p:ssh-client=1 cmd:ssh=1

P:git
D:ssh-client cmd:ssh
"""


def make_archive(text):
    """Упаковать текст индекса в tar.gz, как это делает Alpine."""
    data = text.encode("utf-8")
    buffer = io.BytesIO()
    with tarfile.open(fileobj=buffer, mode="w:gz") as tar:
        info = tarfile.TarInfo("APKINDEX")
        info.size = len(data)
        tar.addfile(info, io.BytesIO(data))
    return buffer.getvalue()


class ApkTest(unittest.TestCase):
    """Проверка разбора APKINDEX."""

    def test_dependency_name(self):
        """Ограничения версий отбрасываются."""
        self.assertEqual(dependency_name("libcurl=8.14"), "libcurl")
        self.assertEqual(dependency_name("zlib>=1.0"), "zlib")
        self.assertEqual(dependency_name("so:libz.so.1"), "so:libz.so.1")
        self.assertEqual(dependency_name("busybox~1.36"), "busybox")

    def test_index_url(self):
        """К URL каталога добавляется имя архива."""
        self.assertEqual(index_url("http://h/main/"),
                         "http://h/main/APKINDEX.tar.gz")
        self.assertEqual(index_url("http://h/x.tar.gz"), "http://h/x.tar.gz")

    def test_dependency_map(self):
        """Виртуальные имена разрешаются, конфликты и петли убираются."""
        deps = build_dependency_map(parse_index(INDEX))
        self.assertEqual(deps["curl"], ["libcurl", "musl", "zlib"])
        self.assertEqual(deps["libcurl"],
                         ["musl", "zlib", "ca-certificates-bundle"])
        self.assertEqual(deps["musl"], [])
        self.assertEqual(deps["zlib"], ["musl"])

    def test_named_virtual(self):
        """Именованное виртуальное имя — вершина со всеми поставщиками."""
        deps = build_dependency_map(parse_index(INDEX))
        self.assertEqual(deps["ssh-client"], ["ssh-default", "ssh-krb5"])
        self.assertEqual(deps["git"], ["ssh-client", "ssh-default"])
        self.assertNotIn("cmd:ssh", deps)

    def test_extract_index(self):
        """Текст индекса извлекается из архива."""
        self.assertEqual(extract_index(make_archive(INDEX)), INDEX)

    def test_bad_archive(self):
        """Повреждённый архив даёт RepositoryError."""
        with self.assertRaises(RepositoryError):
            extract_index(b"not an archive")

    def test_load_repository(self):
        """Индекс загружается по URL (file://) целиком."""
        with tempfile.TemporaryDirectory() as folder:
            path = os.path.join(folder, "APKINDEX.tar.gz")
            Path(path).write_bytes(make_archive(INDEX))
            deps = load_repository(Path(folder).as_uri())
        self.assertIn("curl", deps)

    def test_download_error(self):
        """Недоступный адрес даёт RepositoryError."""
        with self.assertRaises(RepositoryError):
            load_repository("file:///no/such/folder")


if __name__ == "__main__":
    unittest.main()
