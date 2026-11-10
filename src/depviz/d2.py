"""Текстовое представление графа зависимостей на языке диаграмм D2."""

DIRECTION = "direction: right"


def quote(name):
    """Заключить имя пакета в кавычки D2 с экранированием."""
    escaped = name.replace("\\", "\\\\").replace('"', '\\"')
    return f'"{escaped}"'


def to_d2(graph):
    """Вернуть строки описания графа на языке D2.

    Каждое ребро «пакет -> зависимость» записывается отдельной
    строкой. Пакет без зависимостей объявляется отдельно, чтобы
    граф из одной вершины тоже был виден на диаграмме.
    """
    lines = [DIRECTION]
    for name, deps in graph.items():
        if not deps:
            lines.append(quote(name))
        for dep in deps:
            lines.append(f"{quote(name)} -> {quote(dep)}")
    return lines
