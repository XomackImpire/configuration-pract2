"""Загрузка и проверка YAML-конфигурации."""

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

DEFAULT_CONFIG = Path("config.yaml")


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


def _require(data: dict[str, Any], key: str, expected_type: type) -> Any:
    """Проверяет наличие параметра и его тип."""
    if key not in data:
        raise ValueError(f"В конфигурации отсутствует параметр '{key}'")
    value = data[key]
    if not isinstance(value, expected_type):
        raise ValueError(f"Параметр '{key}' должен иметь тип {expected_type.__name__}")
    return value


def load_config(path: str | Path = DEFAULT_CONFIG) -> AppConfig:
    """Читает YAML-файл и проверяет все обязательные настройки."""
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

    if not package:
        raise ValueError("Имя пакета не может быть пустым")
    if not repository_url.startswith(("http://", "https://")):
        raise ValueError("repository_url должен начинаться с http:// или https://")
    if not test_repository:
        raise ValueError("Путь test_repository не может быть пустым")
    if not output_file or Path(output_file).suffix.lower() != ".png":
        raise ValueError("output_file должен задавать имя PNG-файла")
    if max_depth < 0:
        raise ValueError("max_depth не может быть отрицательным")

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
    """Печатает настройки в формате ключ — значение."""
    for key, value in config.__dict__.items():
        print(f"{key}: {value}")
