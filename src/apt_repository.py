"""Самостоятельное чтение индекса пакетов Ubuntu APT."""

import gzip
import re
import urllib.error
import urllib.request
from dataclasses import dataclass
from pathlib import Path

GZIP_MAGIC = b"\x1f\x8b"
HTTP_PREFIXES = ("http://", "https://")
USER_AGENT = "variant25-dependency-visualizer/1.0"
TIMEOUT_SECONDS = 30
PACKAGE_NAME_RE = re.compile(r"([a-z0-9][a-z0-9+.-]*)")


@dataclass(frozen=True)
class PackageInfo:
    """Метаданные одного пакета."""
    name: str
    version: str
    dependencies: tuple[str, ...]


def _read_source(source: str) -> bytes:
    """Читает локальный индекс или загружает по HTTP(S)."""
    if source.startswith(HTTP_PREFIXES):
        content = _download(source)
    else:
        content = _read_local(source)
    return _maybe_decompress(content, source)


def _download(source: str) -> bytes:
    """Загружает индекс по HTTP(S)."""
    request = urllib.request.Request(
        source, headers={"User-Agent": USER_AGENT}
    )
    try:
        with urllib.request.urlopen(
            request, timeout=TIMEOUT_SECONDS
        ) as response:
            return response.read()
    except (urllib.error.URLError, TimeoutError) as error:
        msg = f"Не удалось загрузить индекс APT: {error}"
        raise RuntimeError(msg) from error


def _read_local(source: str) -> bytes:
    """Читает локальный файл."""
    path = Path(source)
    if not path.is_file():
        raise FileNotFoundError(f"Индекс пакетов не найден: {path}")
    return path.read_bytes()


def _maybe_decompress(content: bytes, source: str) -> bytes:
    """Распаковывает gzip, если это нужно."""
    if not (source.endswith(".gz") or content.startswith(GZIP_MAGIC)):
        return content
    try:
        return gzip.decompress(content)
    except OSError as error:
        msg = "Файл .gz не является корректным архивом gzip"
        raise ValueError(msg) from error


def _parse_dependencies(value: str) -> tuple[str, ...]:
    """Извлекает имена пакетов из Depends и Pre-Depends."""
    result: list[str] = []
    for group in value.split(","):
        alternative = group.split("|")[0].strip()
        match = PACKAGE_NAME_RE.match(alternative)
        if match and match.group(1) not in result:
            result.append(match.group(1))
    return tuple(result)


def _parse_stanza(stanza: str) -> dict[str, str]:
    """Разбирает один блок Packages в словарь."""
    fields: dict[str, str] = {}
    current_key = ""
    for line in stanza.splitlines():
        if line[:1].isspace() and current_key:
            fields[current_key] += " " + line.strip()
        elif ":" in line:
            current_key, value = line.split(":", 1)
            fields[current_key] = value.strip()
    return fields


def parse_packages_index(content: bytes) -> dict[str, PackageInfo]:
    """Разбирает текстовый индекс без apt-библиотек."""
    text = content.decode("utf-8", errors="replace")
    stanzas = re.split(r"\n\s*\n", text.strip())
    packages: dict[str, PackageInfo] = {}
    
    for stanza in stanzas:
        fields = _parse_stanza(stanza)
        name = fields.get("Package")
        if not name:
            continue
        
        pre = fields.get("Pre-Depends", "")
        dep = fields.get("Depends", "")
        deps_text = ", ".join(filter(None, [pre, dep]))
        
        packages[name] = PackageInfo(
            name=name,
            version=fields.get("Version", "unknown"),
            dependencies=_parse_dependencies(deps_text),
        )
    return packages


def load_apt_packages(source: str) -> dict[str, PackageInfo]:
    """Загружает и разбирает индекс."""
    return parse_packages_index(_read_source(source))


def get_direct_dependencies(
    packages: dict[str, PackageInfo], package_name: str
) -> tuple[str, ...]:
    """Возвращает прямые зависимости пакета."""
    if package_name not in packages:
        raise KeyError(f"Пакет '{package_name}' не найден в индексе APT")
    return packages[package_name].dependencies