"""CLI-точка входа приложения."""

import argparse
import json
import sys
from pathlib import Path

from .apt_repository import PackageInfo, get_direct_dependencies, load_apt_packages
from .config import load_config, print_config
from .graph import DependencyGraph, build_graph, find_cycles
from .ordering import installation_order
from .visualizer import ascii_tree, render_png, save_plantuml


def load_test_repository(path: str) -> dict[str, tuple[str, ...]]:
    """Загружает тестовый граф из JSON: объект имя -> список зависимостей."""
    file_path = Path(path)
    if not file_path.is_file():
        raise FileNotFoundError(f"Тестовый репозиторий не найден: {file_path}")
    data = json.loads(file_path.read_text(encoding="utf-8"))
    if not isinstance(data, dict) or not data:
        raise ValueError("Тестовый репозиторий должен быть непустым JSON-объектом")
    result: dict[str, tuple[str, ...]] = {}
    for package, dependencies in data.items():
        if not isinstance(package, str) or not package.isalpha() or not package.isupper():
            raise ValueError(f"Имя тестового пакета должно состоять из больших латинских букв: {package}")
        if not isinstance(dependencies, list) or not all(
            isinstance(item, str) and item.isalpha() and item.isupper()
            for item in dependencies
        ):
            raise ValueError(f"Зависимости пакета {package} должны быть списком больших латинских букв")
        result[package] = tuple(dependencies)
    return result


def _test_graph(root: str, data: dict[str, tuple[str, ...]], max_depth: int) -> DependencyGraph:
    """Строит граф из тестового источника тем же алгоритмом BFS."""
    if root not in data:
        raise KeyError(f"Пакет '{root}' отсутствует в тестовом репозитории")
    return build_graph(root, lambda name: data.get(name, ()), max_depth)


def run(config_path: str) -> int:
    """Выполняет все этапы анализа согласно конфигурации."""
    config = load_config(config_path)
    print("Параметры конфигурации:")
    print_config(config)

    if config.test_mode:
        test_data = load_test_repository(config.test_repository)
        graph = _test_graph(config.package, test_data, config.max_depth)
        direct = test_data[config.package]
    else:
        packages = load_apt_packages(config.repository_url)
        direct = get_direct_dependencies(packages, config.package)

        def dependency_loader(name: str) -> tuple[str, ...]:
            info = packages.get(name)
            return info.dependencies if info else ()

        graph = build_graph(config.package, dependency_loader, config.max_depth)

    print("\nПрямые зависимости:")
    print(", ".join(direct) if direct else "Нет прямых зависимостей")

    cycles = find_cycles(graph)
    print("\nЦиклические зависимости:")
    if cycles:
        for cycle in cycles:
            print(" -> ".join(cycle))
    else:
        print("Не обнаружены")

    print("\nПорядок загрузки (зависимости раньше зависимого пакета):")
    try:
        print(" -> ".join(installation_order(graph)))
    except ValueError as error:
        print(f"Не определён: {error}")

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
    return 0


def main() -> int:
    """Разбирает аргументы командной строки."""
    parser = argparse.ArgumentParser(description="Визуализатор зависимостей Ubuntu APT")
    parser.add_argument("-c", "--config", default="config.yaml", help="Путь к YAML-конфигурации")
    args = parser.parse_args()
    try:
        return run(args.config)
    except (ValueError, KeyError, FileNotFoundError, RuntimeError, json.JSONDecodeError) as error:
        print(f"Ошибка: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
