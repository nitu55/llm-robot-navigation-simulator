
class VirtualSensors:
    """
    Simulates four directional distance sensors on a grid.
    Robot position format: (row, col).
    Distance is measured in grid cells.
    """

    def __init__(self, rows, cols, max_range=5):
        self.rows = rows
        self.cols = cols
        self.max_range = max_range

    def measure_direction(self, position, obstacles, direction):
        """Measure distance to the nearest obstacle or grid boundary."""
        row, col = position
        dr, dc = direction

        for distance in range(1, self.max_range + 1):
            next_row = row + dr * distance
            next_col = col + dc * distance

            if not (
                0 <= next_row < self.rows
                and 0 <= next_col < self.cols
            ):
                return distance

            if (next_row, next_col) in obstacles:
                return distance

        return None

    def scan(self, position, obstacles):
        """Return distance readings in all four directions."""
        directions = {
            "north": (-1, 0),
            "south": (1, 0),
            "west": (0, -1),
            "east": (0, 1),
        }

        return {
            name: self.measure_direction(
                position, obstacles, direction
            )
            for name, direction in directions.items()
        }

    def discover_obstacles(self, position, obstacles):
        """
        Return the obstacle cells detected by the sensors.
        Only obstacles within the four sensor directions
        and within the maximum range are discovered.
        """
        discovered = set()
        row, col = position

        directions = [
            (-1, 0),  # North
            (1, 0),   # South
            (0, -1),  # West
            (0, 1),   # East
        ]

        for dr, dc in directions:
            for distance in range(1, self.max_range + 1):
                next_row = row + dr * distance
                next_col = col + dc * distance

                if not (
                    0 <= next_row < self.rows
                    and 0 <= next_col < self.cols
                ):
                    break

                cell = (next_row, next_col)

                if cell in obstacles:
                    discovered.add(cell)
                    break

        return discovered
