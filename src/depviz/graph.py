"""Построение графа зависимостей обходом в ширину (BFS) с рекурсией."""


def bfs_levels(deps, level, graph):
    """Обработать один уровень BFS и рекурсивно перейти к следующему.

    deps — словарь {пакет: список прямых зависимостей};
    level — пакеты текущего уровня;
    graph — уже построенная часть графа. Его ключи служат множеством
    посещённых вершин, поэтому циклы не приводят к зацикливанию.
    """
    if not level:
        return graph
    for package in level:
        graph[package] = list(deps.get(package, []))
    next_level = []
    for package in level:
        for child in graph[package]:
            if child not in graph and child not in next_level:
                next_level.append(child)
    return bfs_levels(deps, next_level, graph)


def build_graph(deps, root):
    """Вернуть граф {пакет: зависимости}, достижимый из пакета root."""
    return bfs_levels(deps, [root], {})


def reverse_map(deps):
    """Развернуть рёбра: {пакет: пакеты, которые от него зависят}."""
    reverse = {}
    for package, children in deps.items():
        reverse.setdefault(package, [])
        for child in children:
            reverse.setdefault(child, []).append(package)
    return reverse


def reverse_dependencies(deps, package):
    """Вернуть все пакеты, которые прямо или транзитивно зависят от package.

    Используется тот же рекурсивный BFS, но по развёрнутому графу.
    """
    graph = build_graph(reverse_map(deps), package)
    return [name for name in graph if name != package]
