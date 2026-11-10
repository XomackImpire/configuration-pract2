"""Построение графа зависимостей алгоритмом BFS без рекурсии."""

from collections import deque
from dataclasses import dataclass, field


@dataclass
class DependencyGraph:
    """Ориентированный граф: пакет -> пакеты, от которых он зависит."""

    root: str
    edges: dict[str, list[str]] = field(default_factory=dict)
    depths: dict[str, int] = field(default_factory=dict)

    def add_node(self, name: str, depth: int) -> None:
        """Добавляет вершину, сохраняя минимальную глубину её обнаружения."""
        self.edges.setdefault(name, [])
        self.depths[name] = min(depth, self.depths.get(name, depth))


def build_graph(root: str, dependency_loader, max_depth: int) -> DependencyGraph:
    """Строит граф в ширину; повторные вершины и циклы не обходятся повторно."""
    if max_depth < 0:
        raise ValueError("Максимальная глубина не может быть отрицательной")

    graph = DependencyGraph(root=root)
    graph.add_node(root, 0)
    queue = deque([root])
    expanded: set[str] = set()

    while queue:
        current = queue.popleft()
        current_depth = graph.depths[current]
        if current in expanded or current_depth >= max_depth:
            continue
        expanded.add(current)

        for dependency in dependency_loader(current):
            if dependency not in graph.edges[current]:
                graph.edges[current].append(dependency)
            if dependency not in graph.depths:
                graph.add_node(dependency, current_depth + 1)
                queue.append(dependency)
    return graph


def find_cycles(graph: DependencyGraph) -> list[list[str]]:
    """Находит циклы в графе итеративным DFS с цветами вершин."""
    color = {node: 0 for node in graph.edges}
    cycles: list[list[str]] = []
    for start in graph.edges:
        if color[start] != 0:
            continue
        stack: list[tuple[str, int]] = [(start, 0)]
        path: list[str] = [start]
        positions = {start: 0}
        color[start] = 1
        while stack:
            node, index = stack[-1]
            neighbors = graph.edges.get(node, [])
            if index >= len(neighbors):
                stack.pop()
                color[node] = 2
                positions.pop(node, None)
                path.pop()
                continue
            neighbor = neighbors[index]
            stack[-1] = (node, index + 1)
            if neighbor not in color:
                continue
            if color[neighbor] == 0:
                color[neighbor] = 1
                positions[neighbor] = len(path)
                path.append(neighbor)
                stack.append((neighbor, 0))
            elif color[neighbor] == 1 and neighbor in positions:
                cycle = path[positions[neighbor]:] + [neighbor]
                if cycle not in cycles:
                    cycles.append(cycle)
    return cycles
