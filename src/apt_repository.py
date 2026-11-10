"""Самостоятельное чтение индекса пакетов Ubuntu APT."""

import gzip
import re
import urllib.error
import urllib.request
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class PackageInfo:
    """Метаданные одного пакета из индекса APT."""

    name: str
    version: str
    dependencies: tuple[str, ...]


def _read_source(source: str) -> bytes:
    """Читает локальный индекс или загружает его по HTTP(S)."""
    if source.startswith(("http://", "https://")):
        request = urllib.request.Request(
            source, headers={"User-Agent": "variant25-dependency-visualizer/1.0"}
        )
        try:
            with urllib.request.urlopen(request, timeout=30) as response:
                content = response.read()
        except (urllib.error.URLError, TimeoutError) as error:
            raise RuntimeError(f"Не удалось загрузить индекс APT: {error}") from error
    else:
        path = Path(source)
        if not path.is_file():
            raise FileNotFoundError(f"Индекс пакетов не найден: {path}")
        content = path.read_bytes()

    if source.endswith(".gz") or content[:2] == b"\x1f\x8b":
        try:
            content = gzip.decompress(content)
        except OSError as error:
            raise ValueError("Файл имеет расширение .gz, но не является корректным gzip") from error
    return content


def _parse_dependencies(value: str) -> tuple[str, ...]:
    """Извлекает имена пакетов из Depends и Pre-Depends.

    Для альтернатив вида 'pkg-a | pkg-b' выбирается первый вариант.
    Ограничения версий и архитектурные условия не вычисляются.
    """
    result: list[str] = []
    for group in value.split(","):
        alternative = group.split("|")[0].strip()
        match = re.match(r"([a-z0-9][a-z0-9+.-]*)", alternative)
        if match:
            name = match.group(1)
            if name not in result:
                result.append(name)
    return tuple(result)


def parse_packages_index(content: bytes) -> dict[str, PackageInfo]:
    """Разбирает текстовый индекс Packages без apt-библиотек."""
    text = content.decode("utf-8", errors="replace")
    stanzas = re.split(r"\n\s*\n", text.strip())
    packages: dict[str, PackageInfo] = {}

    for stanza in stanzas:
        fields: dict[str, str] = {}
        current_key = ""
        for line in stanza.splitlines():
            if line[:1].isspace() and current_key:
                fields[current_key] += " " + line.strip()
                continue
            if ":" not in line:
                continue
            current_key, value = line.split(":", 1)
            fields[current_key] = value.strip()

        name = fields.get("Package")
        if not name:
            continue
        dependencies_text = ", ".join(
            value for value in (fields.get("Pre-Depends"), fields.get("Depends"))
            if value
        )
        packages[name] = PackageInfo(
            name=name,
            version=fields.get("Version", "unknown"),
            dependencies=_parse_dependencies(dependencies_text),
        )
    return packages


def load_apt_packages(source: str) -> dict[str, PackageInfo]:
    """Загружает и разбирает индекс APT по URL или локальному пути."""
    return parse_packages_index(_read_source(source))


def get_direct_dependencies(
    packages: dict[str, PackageInfo], package_name: str
) -> tuple[str, ...]:
    """Возвращает прямые зависимости указанного пакета."""
    if package_name not in packages:
        raise KeyError(f"Пакет '{package_name}' не найден в индексе APT")
    return packages[package_name].dependencies
