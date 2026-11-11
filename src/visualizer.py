"""Формирование PlantUML, PNG и ASCII-представления."""

import shutil
import subprocess
from pathlib import Path

from .graph import DependencyGraph

SUCCESS_CODE = 0
PLANTUML_FORMAT = "png"
INDENT = "    "
TREE_PREFIX = "└── "


def _escape_label(value: str) -> str:
    """Экранирует символы для PlantUML."""
    return value.replace("\\", "\\\\").replace('"', '\\"')


def _safe_id(value: str) -> str:
    """Безопасный идентификатор."""
    safe_chars = (c if c.isalnum() else "_" for c in value)
    return "P" + "".join(safe_chars)


def to_plantuml(graph: DependencyGraph) -> str:
    """Создаёт текст PlantUML."""
    lines = [
        "@startuml",
        "left to right direction",
        "skinparam packageStyle rectangle",
    ]
    for node in graph.edges:
        label = _escape_label(node)
        lines.append(f'component "{label}" as N{_safe_id(node)}')
        
    for source, dependencies in graph.edges.items():
        for target in dependencies:
            src_id = _safe_id(source)
            tgt_id = _safe_id(target)
            lines.append(f"N{src_id} --> N{tgt_id}")
            
    lines.append("@enduml")
    return "\n".join(lines) + "\n"


def save_plantuml(graph: DependencyGraph, output_file: str) -> Path:
    """Сохраняет исходник диаграммы."""
    path = Path(output_file).with_suffix(".puml")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(to_plantuml(graph), encoding="utf-8")
    return path


def render_png(plantuml_file: Path, output_file: str) -> None:
    """Рендерит PNG через PlantUML."""
    executable = shutil.which("plantuml")
    if not executable:
        msg = (
            "Команда plantuml не найдена. Установите PlantUML и Java; "
            f"исходник сохранён в {plantuml_file}"
        )
        raise RuntimeError(msg)
        
    target_dir = str(Path(output_file).resolve().parent)
    command = [
        executable,
        f"-t{PLANTUML_FORMAT}",
        "-o",
        target_dir,
        str(plantuml_file.resolve()),
    ]
    result = subprocess.run(command, capture_output=True, text=True)
    _check_plantuml_result(result)
    _move_generated_png(plantuml_file, output_file)


def _check_plantuml_result(result) -> None:
    """Проверяет код возврата."""
    if result.returncode != SUCCESS_CODE:
        msg = result.stderr.strip() or result.stdout.strip()
        raise RuntimeError(f"Ошибка PlantUML: {msg}")


def _move_generated_png(plantuml_file: Path, output_file: str) -> None:
    """Перемещает сгенерированный PNG."""
    generated = plantuml_file.with_suffix(".png")
    target = Path(output_file)
    if generated.resolve() != target.resolve() and generated.exists():
        generated.replace(target)
    if not target.is_file():
        raise RuntimeError("PlantUML завершился, но PNG не был создан")


def ascii_tree(graph: DependencyGraph) -> str:
    """Возвращает дерево зависимостей."""
    lines = [graph.root]
    expanded: set[str] = set()
    stack: list[tuple[str, str, frozenset[str]]] = []
    for child in reversed(graph.edges.get(graph.root, [])):
        stack.append((child, "", frozenset({graph.root})))
        
    while stack:
        node, prefix, ancestors = stack.pop()
        line, skip = _format_tree_line(node, prefix, ancestors, expanded)
        lines.append(line)
        if skip:
            continue
        expanded.add(node)
        next_ancestors = ancestors | {node}
        for child in reversed(graph.edges.get(node, [])):
            stack.append((child, prefix + INDENT, next_ancestors))
    return "\n".join(lines)


def _format_tree_line(node, prefix, ancestors, expanded) -> tuple[str, bool]:
    """Форматирует строку дерева."""
    if node in ancestors:
        return f"{prefix}{TREE_PREFIX}{node} [cycle]", True
    if node in expanded:
        return f"{prefix}{TREE_PREFIX}{node} [already shown]", True
    return f"{prefix}{TREE_PREFIX}{node}", False