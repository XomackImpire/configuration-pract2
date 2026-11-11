"""Построение графа зависимостей алгоритмом BFS без рекурсии."""

from collections import deque
from dataclasses import dataclass, field

MIN_DEPTH = 0
WHITE = 0
GRAY = 1
BLACK = 2


@dataclass
class DependencyGraph:
    """Ориентированный граф: пакет -> пакеты, от которых он зависит."""

    root: str
    edges: dict[str, list[str]] = field(default_factory=dict)
    depths: dict[str, int] = field(default_factory=dict)

    def add_node(self, name: str, depth: int) -> None:
        """Добавляет вершину, сохраняя минимальную глубину."""
        self.edges.setdefault(name, [])
        self.depths[name] = min(depth, self.depths.get(name, depth))


def build_graph(root: str, loader, max_depth: int) -> DependencyGraph:
    """Строит граф в ширину."""
    if max_depth < MIN_DEPTH:
        raise ValueError("Максимальная глубина не может быть отрицательной")

    graph = DependencyGraph(root=root)
    graph.add_node(root, MIN_DEPTH)
    queue = deque([root])
    expanded: set[str] = set()

    while queue:
        current = queue.popleft()
        current_depth = graph.depths[current]
        if current in expanded or current_depth >= max_depth:
            continue
        expanded.add(current)
        _expand_node(graph, current, current_depth, loader, queue)
    return graph


def _expand_node(graph, node, depth, loader, queue) -> None:
    """Добавляет зависимости узла в граф и очередь."""
    for dependency in loader(node):
        if dependency not in graph.edges[node]:
            graph.edges[node].append(dependency)
        if dependency not in graph.depths:
            graph.add_node(dependency, depth + 1)
            queue.append(dependency)


def find_cycles(graph: DependencyGraph) -> list[list[str]]:
    """Находит циклы в графе итеративным DFS."""
    color = {node: WHITE for node in graph.edges}
    cycles: list[list[str]] = []
    for start in graph.edges:
        if color[start] == WHITE:
            _dfs_cycles(graph, start, color, cycles)
    return cycles


def _dfs_cycles(graph, start, color, cycles) -> None:
    """Итеративный DFS для поиска циклов."""
    stack: list[tuple[str, int]] = [(start, 0)]
    path: list[str] = [start]
    positions = {start: 0}
    color[start] = GRAY

    while stack:
        node, index = stack[-1]
        neighbors = graph.edges.get(node, [])
        
        if index >= len(neighbors):
            stack.pop()
            color[node] = BLACK
            positions.pop(node, None)
            path.pop()
            continue
            
        neighbor = neighbors[index]
        stack[-1] = (node, index + 1)
        
        if neighbor not in color:
            continue
            
        if color[neighbor] == WHITE:
            _visit_neighbor(neighbor, path, positions, stack, color)
        elif color[neighbor] == GRAY and neighbor in positions:
            _record_cycle(path, positions[neighbor], cycles)


def _visit_neighbor(neighbor, path, positions, stack, color) -> None:
    """Переход к новому узлу."""
    color[neighbor] = GRAY
    positions[neighbor] = len(path)
    path.append(neighbor)
    stack.append((neighbor, 0))


def _record_cycle(path: list[str], start_index: int, cycles: list) -> None:
    """Сохраняет найденный цикл."""
    new_cycle = path[start_index:] + [path[start_index]]
    if new_cycle not in cycles:
        cycles.append(new_cycle)