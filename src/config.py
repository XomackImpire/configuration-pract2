"""Загрузка и проверка YAML-конфигурации."""

from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

import yaml

DEFAULT_CONFIG = Path("config.yaml")
MIN_DEPTH = 0


@dataclass(frozen=True)
class AppConfig:
    """Параметры запуска приложения."""
    package: str
    repository_url: str
    test_mode: bool
    test_repository: str
    output_file: str
    show_ascii: bool
    max_depth: int


def _require(data: dict[str, Any], key: str, exp_type: type) -> Any:
    """Проверяет наличие параметра и его тип."""
    if key not in data:
        raise ValueError(f"В конфигурации нет параметра '{key}'")
    value = data[key]
    if not isinstance(value, exp_type):
        type_name = exp_type.__name__
        raise ValueError(f"Параметр '{key}' должен иметь тип {type_name}")
    return value


def _validate_basic(pkg: str, url: str, out: str) -> None:
    """Проверяет строковые параметры."""
    if not pkg:
        raise ValueError("Имя пакета не может быть пустым")
    if not url.startswith(("http://", "https://")):
        raise ValueError("repository_url должен начинаться с http://")
    if not out or Path(out).suffix.lower() != ".png":
        raise ValueError("output_file должен быть PNG-файлом")


def _validate_depth(depth: int) -> None:
    """Проверяет глубину."""
    if depth < MIN_DEPTH:
        raise ValueError("max_depth не может быть отрицательным")


def _validate_test_mode(test_mode: bool, test_repo: str) -> None:
    """Проверяет тестовый репозиторий."""
    if test_mode and not test_repo:
        raise ValueError("test_repository обязателен при test_mode: true")


def load_config(path: str | Path = DEFAULT_CONFIG) -> AppConfig:
    """Читает YAML-файл и проверяет настройки."""
    config_path = Path(path)
    if not config_path.is_file():
        raise FileNotFoundError(f"Файл конфигурации не найден: {config_path}")

    with config_path.open("r", encoding="utf-8") as file:
        data = yaml.safe_load(file)

    if not isinstance(data, dict):
        raise ValueError("Корень YAML-конфигурации должен быть словарём")

    package = _require(data, "package", str).strip()
    repository_url = _require(data, "repository_url", str).strip()
    test_mode = _require(data, "test_mode", bool)
    test_repository = _require(data, "test_repository", str).strip()
    output_file = _require(data, "output_file", str).strip()
    show_ascii = _require(data, "show_ascii", bool)
    max_depth = _require(data, "max_depth", int)

    _validate_basic(package, repository_url, output_file)
    _validate_depth(max_depth)
    _validate_test_mode(test_mode, test_repository)

    return AppConfig(
        package=package,
        repository_url=repository_url,
        test_mode=test_mode,
        test_repository=test_repository,
        output_file=output_file,
        show_ascii=show_ascii,
        max_depth=max_depth,
    )


def print_config(config: AppConfig) -> None:
    """Печатает настройки."""
    for key, value in asdict(config).items():
        print(f"{key}: {value}")