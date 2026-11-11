"""Точка входа приложения: чтение YAML и выполнение анализа."""

import json
import sys
from pathlib import Path

from .apt_repository import get_direct_dependencies, load_apt_packages
from .config import AppConfig, load_config, print_config
from .graph import DependencyGraph, build_graph, find_cycles
from .ordering import installation_order
from .visualizer import ascii_tree, render_png, save_plantuml

CONFIG_PATH = Path("config.yaml")


def _is_valid_test_name(name: str) -> bool:
    """Проверяет, что имя состоит только из больших латинских букв."""
    return isinstance(name, str) and name.isalpha() and name.isupper()


def _validate_test_data(
    package: str, dependencies: list
) -> None:
    """Проверяет корректность данных тестового пакета."""
    if not _is_valid_test_name(package):
        raise ValueError(f"Некорректное имя пакета: {package}")
    if not isinstance(dependencies, list):
        raise ValueError(f"Зависимости {package} должны быть списком")
    for item in dependencies:
        if not _is_valid_test_name(item):
            raise ValueError(f"Некорректная зависимость {item} пакета {package}")


def load_test_repository(path: str) -> dict[str, tuple[str, ...]]:
    """Загружает тестовый граф из JSON: имя -> список зависимостей."""
    file_path = Path(path)
    if not file_path.is_file():
        raise FileNotFoundError(f"Тестовый репозиторий не найден: {file_path}")
    
    data = json.loads(file_path.read_text(encoding="utf-8"))
    if not isinstance(data, dict) or not data:
        raise ValueError("Репозиторий должен быть непустым JSON-объектом")
    
    result: dict[str, tuple[str, ...]] = {}
    for package, dependencies in data.items():
        _validate_test_data(package, dependencies)
        result[package] = tuple(dependencies)
    return result


def _build_test_graph(config: AppConfig, data: dict) -> DependencyGraph:
    """Строит граф по тестовому JSON."""
    if config.package not in data:
        raise KeyError(f"Пакет '{config.package}' отсутствует в репозитории")
    return build_graph(
        config.package, 
        lambda name: data.get(name, ()), 
        config.max_depth
    )


def _build_real_graph(config: AppConfig) -> tuple:
    """Загружает APT и строит реальный граф."""
    packages = load_apt_packages(config.repository_url)
    direct = get_direct_dependencies(packages, config.package)

    def loader(name: str) -> tuple[str, ...]:
        info = packages.get(name)
        return info.dependencies if info else ()

    graph = build_graph(config.package, loader, config.max_depth)
    return graph, direct


def _print_order(graph: DependencyGraph) -> None:
    """Печатает порядок загрузки зависимостей."""
    print("\nПорядок загрузки (зависимости раньше зависимого пакета):")
    try:
        print(" -> ".join(installation_order(graph)))
    except ValueError as error:
        print(f"Не определён: {error}")


def _print_visual(graph: DependencyGraph, config: AppConfig) -> None:
    """Печатает ASCII-дерево и сохраняет PlantUML/PNG."""
    if config.show_ascii:
        print("\nASCII-дерево:")
        print(ascii_tree(graph))
    
    plantuml_file = save_plantuml(graph, config.output_file)
    print(f"\nИсходный файл PlantUML: {plantuml_file}")
    
    try:
        render_png(plantuml_file, config.output_file)
        print(f"Изображение графа: {config.output_file}")
    except RuntimeError as error:
        print(f"Предупреждение: {error}", file=sys.stderr)


def run() -> int:
    """Выполняет все этапы анализа согласно YAML-конфигурации."""
    config = load_config(CONFIG_PATH)
    print("Параметры конфигурации:")
    print_config(config)

    if config.test_mode:
        data = load_test_repository(config.test_repository)
        graph = _build_test_graph(config, data)
        direct = data[config.package]
    else:
        graph, direct = _build_real_graph(config)

    print("\nПрямые зависимости:")
    print(", ".join(direct) if direct else "Нет прямых зависимостей")

    cycles = find_cycles(graph)
    print("\nЦиклические зависимости:")
    if cycles:
        for cycle in cycles:
            print(" -> ".join(cycle))
    else:
        print("Не обнаружены")

    _print_order(graph)
    _print_visual(graph, config)
    return 0


def main() -> int:
    """Точка входа без CLI-аргументов: параметры берутся из config.yaml."""
    try:
        return run()
    except Exception as error:
        print(f"Ошибка: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())