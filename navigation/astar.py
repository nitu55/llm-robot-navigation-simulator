
import heapq


def heuristic(a, b):
    """Manhattan distance between two grid cells."""
    return abs(a[0] - b[0]) + abs(a[1] - b[1])


def find_path(start, goal, obstacles, rows, cols):
    """
    Return a shortest path from start to goal using A*.

    Positions use (row, column).
    Obstacles is a set of blocked (row, column) cells.
    Returns a list of positions, excluding start, or None.
    """

    if start == goal:
        return []

    if (
        not (0 <= goal[0] < rows and 0 <= goal[1] < cols)
        or goal in obstacles
    ):
        return None

    open_heap = []
    heapq.heappush(
        open_heap,
        (heuristic(start, goal), 0, start)
    )

    came_from = {}
    g_score = {start: 0}
    closed = set()
    counter = 0

    directions = [
        (-1, 0),  # Up
        (1, 0),   # Down
        (0, -1),  # Left
        (0, 1),   # Right
    ]

    while open_heap:
        _, _, current = heapq.heappop(open_heap)

        if current in closed:
            continue

        if current == goal:
            path = []

            while current != start:
                path.append(current)
                current = came_from[current]

            path.reverse()
            return path

        closed.add(current)

        for dr, dc in directions:
            neighbor = (current[0] + dr, current[1] + dc)

            if not (
                0 <= neighbor[0] < rows
                and 0 <= neighbor[1] < cols
            ):
                continue

            if neighbor in obstacles or neighbor in closed:
                continue

            tentative_g = g_score[current] + 1

            if tentative_g < g_score.get(neighbor, float("inf")):
                came_from[neighbor] = current
                g_score[neighbor] = tentative_g

                counter += 1
                f_score = tentative_g + heuristic(neighbor, goal)

                heapq.heappush(
                    open_heap,
                    (f_score, counter, neighbor)
                )

    return None
