"""Вычисление порядка загрузки зависимостей."""

from .graph import DependencyGraph


def installation_order(graph: DependencyGraph) -> list[str]:
    """Возвращает зависимости раньше пакетов, которые от них зависят.

    При наличии цикла возвращает порядок для ациклической части и поднимает
    ValueError с описанием циклического набора.
    """
    visited: set[str] = set()
    active: set[str] = set()
    result: list[str] = []
    for start in graph.edges:
        if start in visited:
            continue
        stack: list[tuple[str, bool]] = [(start, False)]
        while stack:
            node, exiting = stack.pop()
            if exiting:
                active.discard(node)
                if node not in visited:
                    visited.add(node)
                    result.append(node)
                continue
            if node in visited:
                continue
            if node in active:
                raise ValueError("Невозможно определить полный порядок: обнаружен цикл")
            active.add(node)
            stack.append((node, True))
            for dependency in reversed(graph.edges.get(node, [])):
                if dependency in active:
                    raise ValueError("Невозможно определить полный порядок: обнаружен цикл")
                if dependency not in visited:
                    stack.append((dependency, False))
    return result
