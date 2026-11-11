"""Вычисление порядка загрузки зависимостей."""

from .graph import DependencyGraph

CYCLE_ERROR = "Невозможно определить порядок: обнаружен цикл"


def installation_order(graph: DependencyGraph) -> list[str]:
    """Возвращает зависимости раньше пакетов, которые от них зависят."""
    visited: set[str] = set()
    active: set[str] = set()
    result: list[str] = []
    
    for start in graph.edges:
        if start not in visited:
            _traverse(graph, start, visited, active, result)
    return result


def _traverse(graph, start, visited, active, result) -> None:
    """Итеративный обход из одной вершины."""
    stack: list[tuple[str, bool]] = [(start, False)]
    while stack:
        node, exiting = stack.pop()
        if exiting:
            _finish_node(node, visited, active, result)
            continue
        _enter_node(graph, node, visited, active, stack)


def _enter_node(graph, node, visited, active, stack) -> None:
    """Обработка входа в вершину."""
    if node in visited:
        return
    if node in active:
        raise ValueError(CYCLE_ERROR)
        
    active.add(node)
    stack.append((node, True))
    _push_dependencies(graph, node, visited, active, stack)


def _push_dependencies(graph, node, visited, active, stack) -> None:
    """Добавляет зависимости в стек."""
    for dependency in reversed(graph.edges.get(node, [])):
        if dependency in active:
            raise ValueError(CYCLE_ERROR)
        if dependency not in visited:
            stack.append((dependency, False))


def _finish_node(node, visited, active, result) -> None:
    """Обработка выхода из вершины."""
    active.discard(node)
    if node not in visited:
        visited.add(node)
        result.append(node)