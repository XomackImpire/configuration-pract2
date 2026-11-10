"""Формирование PlantUML, PNG и ASCII-представления графа."""

import shutil
import subprocess
from pathlib import Path

from .graph import DependencyGraph


def _escape_label(value: str) -> str:
    """Экранирует символы, значимые для PlantUML."""
    return value.replace('\\', '\\\\').replace('"', '\\"')


def to_plantuml(graph: DependencyGraph) -> str:
    """Создаёт исходный текст PlantUML для графа зависимостей."""
    lines = ["@startuml", "left to right direction", "skinparam packageStyle rectangle"]
    for node in graph.edges:
        lines.append(f'component "{_escape_label(node)}" as N{_safe_id(node)}')
    for source, dependencies in graph.edges.items():
        for target in dependencies:
            lines.append(f"N{_safe_id(source)} --> N{_safe_id(target)}")
    lines.append("@enduml")
    return "\n".join(lines) + "\n"


def _safe_id(value: str) -> str:
    """Преобразует имя пакета в стабильный безопасный идентификатор."""
    return "P" + "".join(char if char.isalnum() else "_" for char in value)


def save_plantuml(graph: DependencyGraph, output_file: str) -> Path:
    """Сохраняет исходник диаграммы рядом с PNG-файлом."""
    path = Path(output_file).with_suffix(".puml")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(to_plantuml(graph), encoding="utf-8")
    return path


def render_png(plantuml_file: Path, output_file: str) -> None:
    """Рендерит PNG установленной командой plantuml.

    Для рендеринга требуются Java и PlantUML, доступный в PATH.
    """
    executable = shutil.which("plantuml")
    if not executable:
        raise RuntimeError(
            "Команда plantuml не найдена. Установите PlantUML и Java; "
            f"исходник диаграммы сохранён в {plantuml_file}"
        )
    result = subprocess.run(
        [executable, "-tpng", "-o", str(Path(output_file).resolve().parent),
         str(plantuml_file.resolve())],
        capture_output=True, text=True, check=False,
    )
    if result.returncode != 0:
        raise RuntimeError(f"Ошибка PlantUML: {result.stderr.strip() or result.stdout.strip()}")
    generated = plantuml_file.with_suffix(".png")
    target = Path(output_file)
    if generated.resolve() != target.resolve() and generated.exists():
        generated.replace(target)
    if not target.is_file():
        raise RuntimeError("PlantUML завершился, но PNG-файл не был создан")


def ascii_tree(graph: DependencyGraph) -> str:
    """Возвращает дерево зависимостей с защитой от повторов и циклов."""
    lines = [graph.root]
    expanded: set[str] = set()
    stack: list[tuple[str, str, frozenset[str]]] = []
    for child in reversed(graph.edges.get(graph.root, [])):
        stack.append((child, "", frozenset({graph.root})))
    while stack:
        node, prefix, ancestors = stack.pop()
        cycle_mark = " [cycle]" if node in ancestors else ""
        repeated_mark = " [already shown]" if node in expanded and not cycle_mark else ""
        lines.append(f"{prefix}└── {node}{cycle_mark}{repeated_mark}")
        if cycle_mark or repeated_mark:
            continue
        expanded.add(node)
        next_ancestors = ancestors | {node}
        for child in reversed(graph.edges.get(node, [])):
            stack.append((child, prefix + "    ", next_ancestors))
    return "\n".join(lines)
