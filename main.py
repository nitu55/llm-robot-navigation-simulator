import pygame
import sys
from concurrent.futures import ThreadPoolExecutor

from navigation.astar import find_path
from robot.sensors import VirtualSensors
from llm_controller import interpret_command


# ============================================================
# 1. INITIALIZATION
# ============================================================

pygame.init()

ROWS = 15
COLS = 20
CELL_SIZE = 40
AXIS_MARGIN = 30

GRID_WIDTH = AXIS_MARGIN + COLS * CELL_SIZE
GRID_HEIGHT = AXIS_MARGIN + ROWS * CELL_SIZE

PANEL_WIDTH = 300
PANEL_X = GRID_WIDTH

SCREEN_WIDTH = GRID_WIDTH + PANEL_WIDTH
SCREEN_HEIGHT = 850

screen = pygame.display.set_mode(
    (SCREEN_WIDTH, SCREEN_HEIGHT)
)
pygame.display.set_caption(
    "LLM-Powered Robot Navigation Simulator"
)

clock = pygame.time.Clock()

WHITE = (245, 245, 245)
BLACK = (25, 25, 25)
GRAY = (180, 180, 180)
LIGHT_GRAY = (230, 230, 230)
GREEN = (30, 180, 80)
RED = (220, 60, 60)
BLUE = (50, 110, 230)
YELLOW = (255, 210, 50)
DARK_BLUE = (35, 55, 85)
ORANGE = (240, 145, 35)

font = pygame.font.SysFont("arial", 18)
small_font = pygame.font.SysFont("arial", 15)
title_font = pygame.font.SysFont("arial", 21, bold=True)


# ============================================================
# 2. ROBOT AND ENVIRONMENT
# ============================================================

start_pos = (1, 1)
robot_pos = start_pos
goal_pos = (12, 18)

obstacles = {
    (3, 3), (3, 4), (3, 5),
    (4, 5), (5, 5),
    (7, 8), (8, 8), (9, 8),
    (10, 12), (10, 13), (10, 14)
}

# Obstacles discovered by the robot's sensors.
known_obstacles = set()

sensors = VirtualSensors(
    rows=ROWS,
    cols=COLS,
    max_range=5
)

sensor_readings = sensors.scan(robot_pos, obstacles)

auto_path = []
auto_running = False
edit_mode = False

message = "Ready"
# Recent navigation events
decision_log = ["Simulation initialized"]
MAX_LOG_ENTRIES = 6


def log_decision(text):
    """Store recent robot decisions for display."""
    decision_log.append(text)

    if len(decision_log) > MAX_LOG_ENTRIES:
        decision_log.pop(0)
last_move_time = 0
MOVE_INTERVAL = 250


# ============================================================
# 3. LLM STATE AND BACKGROUND WORKER
# ============================================================

command_input = ""
command_active = False
llm_status = "Enter a navigation command"

executor = ThreadPoolExecutor(max_workers=1)
llm_future = None


# ============================================================
# 4. BUTTONS AND INPUT BOX
# ============================================================

button_up = pygame.Rect(PANEL_X + 105, 78, 80, 35)
button_left = pygame.Rect(PANEL_X + 25, 118, 80, 35)
button_down = pygame.Rect(PANEL_X + 110, 118, 80, 35)
button_right = pygame.Rect(PANEL_X + 195, 118, 80, 35)

button_auto = pygame.Rect(PANEL_X + 20, 165, 260, 38)
button_stop = pygame.Rect(PANEL_X + 20, 210, 260, 38)
button_reset = pygame.Rect(PANEL_X + 20, 255, 260, 38)
button_edit = pygame.Rect(PANEL_X + 20, 300, 260, 38)

command_box = pygame.Rect(
    PANEL_X + 15, 695, PANEL_WIDTH - 30, 38
)

send_button = pygame.Rect(
    PANEL_X + 15, 740, PANEL_WIDTH - 30, 38
)


# ============================================================
# 5. A* NAVIGATION
# ============================================================

def update_sensor_map():
    """Scan in four directions and add detected obstacles to the local map."""
    global known_obstacles, sensor_readings

    sensor_readings = sensors.scan(robot_pos, obstacles)
    discovered = sensors.discover_obstacles(robot_pos, obstacles)
    known_obstacles.update(discovered)



def start_auto_navigation():
    global auto_path, auto_running, message, last_move_time

    log_decision(f"Planning route to {goal_pos}")

    path = find_path(
        robot_pos,
        goal_pos,
        known_obstacles,
        ROWS,
        COLS
    )

    if robot_pos == goal_pos:
        auto_path = []
        auto_running = False
        message = "Goal reached!"
        log_decision("Goal reached!")

    elif path is None:
        auto_path = []
        auto_running = False
        message = "No path available"
        log_decision("No path through known obstacles")

    else:
        auto_path = path
        auto_running = True
        last_move_time = pygame.time.get_ticks()
        message = "Auto navigation active"
        log_decision(f"Route calculated: {len(path)} steps")


def move_robot(direction):
    global robot_pos, message

    dr, dc = direction
    row, col = robot_pos

    new_pos = (row + dr, col + dc)

    if not (
        0 <= new_pos[0] < ROWS
        and 0 <= new_pos[1] < COLS
    ):
        message = "Grid boundary detected"
        return

    if new_pos in obstacles:
        message = "Obstacle detected!"
        return

    robot_pos = new_pos

    if robot_pos == goal_pos:
        message = "Goal reached!"
    else:
        message = f"Robot moved to {robot_pos}"


# ============================================================
# 6. OBSTACLE EDITING
# ============================================================

def toggle_obstacle_at_pixel(pos):
    global message

    x, y = pos

    # Convert screen coordinates to grid coordinates.
    grid_x = x - AXIS_MARGIN
    grid_y = y - AXIS_MARGIN

    # Ignore clicks on the axes or outside the grid.
    if not (
        0 <= grid_x < COLS * CELL_SIZE
        and 0 <= grid_y < ROWS * CELL_SIZE
    ):
        return

    col = grid_x // CELL_SIZE
    row = grid_y // CELL_SIZE
    cell = (row, col)

    if cell == robot_pos or cell == goal_pos:
        message = "Cannot place obstacle here"
        return

    if cell in obstacles:
        obstacles.remove(cell)
        message = "Obstacle removed"
    else:
        obstacles.add(cell)
        message = "Obstacle added"

    if auto_running:
        start_auto_navigation()


# ============================================================
# 7. LLM COMMAND HANDLING
# ============================================================

def submit_llm_command():
    global llm_future, llm_status, command_input

    if llm_future is not None:
        if not llm_future.done():
            llm_status = "Please wait for current request"
            return

    if not command_input.strip():
        llm_status = "Please enter a command"
        return

    user_command = command_input.strip()

    # Run the API request in the background.
    llm_future = executor.submit(
        interpret_command,
        user_command
    )

    llm_status = "Nemotron is processing..."
    command_input = ""


def handle_llm_result():
    global llm_future, llm_status
    global goal_pos

    if llm_future is None or not llm_future.done():
        return

    completed_future = llm_future
    llm_future = None

    try:
        result = completed_future.result()

        if not isinstance(result, dict):
            llm_status = "Invalid LLM response"
            return

        if result.get("valid") is not True:
            llm_status = str(
                result.get("message", "Command rejected")
            )
            return

        if result.get("action") != "navigate":
            llm_status = "Unsupported action"
            return

        row = result.get("goal_row")
        col = result.get("goal_col")

        if (
            isinstance(row, bool)
            or not isinstance(row, int)
            or isinstance(col, bool)
            or not isinstance(col, int)
        ):
            llm_status = "Invalid coordinates"
            return

        if not (0 <= row < ROWS and 0 <= col < COLS):
            llm_status = "Destination outside grid"
            return

        new_goal = (row, col)

        if new_goal in obstacles:
            llm_status = "Destination is blocked"
            return

        goal_pos = new_goal

        start_auto_navigation()

        if robot_pos == goal_pos:
            llm_status = "Already at destination"
        elif auto_running:
            llm_status = f"Route planned: {goal_pos}"
        else:
            llm_status = "No route available"

    except Exception as error:
        print("LLM request failed:", error)
        llm_status = "LLM failed; check terminal"


# ============================================================
# 8. DRAWING HELPERS
# ============================================================

def draw_text(text, x, y, color=BLACK, font_obj=font):
    image = font_obj.render(str(text), True, color)
    screen.blit(image, (x, y))


def draw_button(rect, label, color=BLUE):
    mouse_pos = pygame.mouse.get_pos()

    if rect.collidepoint(mouse_pos):
        color = tuple(
            min(channel + 25, 255)
            for channel in color
        )

    pygame.draw.rect(
        screen, color, rect, border_radius=6
    )
    pygame.draw.rect(
        screen, BLACK, rect, 1, border_radius=6
    )

    image = font.render(label, True, WHITE)
    screen.blit(image, image.get_rect(center=rect.center))


# ============================================================
# 9. GRID, COORDINATE AXES, ROBOT AND GOAL
# ============================================================

def draw_grid():
    # Column labels along the top axis.
    for col in range(COLS):
        label = small_font.render(str(col), True, BLACK)

        x = AXIS_MARGIN + col * CELL_SIZE + CELL_SIZE // 2
        y = AXIS_MARGIN // 2

        screen.blit(
            label,
            label.get_rect(center=(x, y))
        )

    # Row labels along the left axis.
    for row in range(ROWS):
        label = small_font.render(str(row), True, BLACK)

        x = AXIS_MARGIN // 2
        y = AXIS_MARGIN + row * CELL_SIZE + CELL_SIZE // 2

        screen.blit(
            label,
            label.get_rect(center=(x, y))
        )

    # Draw grid cells.
    for row in range(ROWS):
        for col in range(COLS):
            cell = (row, col)

            rect = pygame.Rect(
                AXIS_MARGIN + col * CELL_SIZE,
                AXIS_MARGIN + row * CELL_SIZE,
                CELL_SIZE,
                CELL_SIZE
            )

            color = WHITE

            if cell in known_obstacles:
                color = RED
            elif cell in obstacles:
                color = GRAY
            elif cell == goal_pos:
                color = BLUE
            elif auto_running and cell in auto_path:
                color = YELLOW

            pygame.draw.rect(screen, color, rect)
            pygame.draw.rect(screen, GRAY, rect, 1)

    # Robot.
    robot_rect = pygame.Rect(
        AXIS_MARGIN + robot_pos[1] * CELL_SIZE + 5,
        AXIS_MARGIN + robot_pos[0] * CELL_SIZE + 5,
        CELL_SIZE - 10,
        CELL_SIZE - 10
    )

    pygame.draw.rect(
        screen, GREEN, robot_rect, border_radius=8
    )

    robot_label = small_font.render("R", True, WHITE)
    screen.blit(
        robot_label,
        robot_label.get_rect(center=robot_rect.center)
    )

    # Goal.
    goal_rect = pygame.Rect(
        AXIS_MARGIN + goal_pos[1] * CELL_SIZE,
        AXIS_MARGIN + goal_pos[0] * CELL_SIZE,
        CELL_SIZE,
        CELL_SIZE
    )

    goal_label = small_font.render("G", True, WHITE)
    screen.blit(
        goal_label,
        goal_label.get_rect(center=goal_rect.center)
    )
    # Goal.
    goal_rect = pygame.Rect(
        AXIS_MARGIN + goal_pos[1] * CELL_SIZE,
        AXIS_MARGIN + goal_pos[0] * CELL_SIZE,
        CELL_SIZE,
        CELL_SIZE
    )

    goal_label = small_font.render("G", True, WHITE)
    screen.blit(
        goal_label,
        goal_label.get_rect(center=goal_rect.center)
    )

    # Draw virtual sensor rays
    robot_center = (
        AXIS_MARGIN + robot_pos[1] * CELL_SIZE + CELL_SIZE // 2,
        AXIS_MARGIN + robot_pos[0] * CELL_SIZE + CELL_SIZE // 2
    )

    directions = [
        (-1, 0),  # North
        (1, 0),   # South
        (0, -1),  # West
        (0, 1),   # East
    ]

    for dr, dc in directions:
        for distance in range(1, sensors.max_range + 1):
            row = robot_pos[0] + dr * distance
            col = robot_pos[1] + dc * distance

            if not (0 <= row < ROWS and 0 <= col < COLS):
                break

            if (row, col) in obstacles:
                break

            target = (
                AXIS_MARGIN + col * CELL_SIZE + CELL_SIZE // 2,
                AXIS_MARGIN + row * CELL_SIZE + CELL_SIZE // 2
            )

            pygame.draw.line(
                screen,
                (30, 150, 240),
                robot_center,
                target,
                3
            )




# ============================================================
# 10. VIRTUAL SENSORS
# ============================================================

def draw_sensor_readings():
    global sensor_readings

    sensor_readings = sensors.scan(robot_pos, obstacles)

    x = PANEL_X + 15
    y = 405

    draw_text(
        "VIRTUAL SENSORS",
        x, y, DARK_BLUE, title_font
    )

    draw_text(
        "Detection range: 5 cells",
        x, y + 27, BLACK, small_font
    )

    directions = [
        ("North", "north"),
        ("South", "south"),
        ("West", "west"),
        ("East", "east")
    ]

    for i, (label, direction) in enumerate(directions):
        distance = sensor_readings[direction]

        if distance is None:
            value = "Clear"
            color = GREEN
        else:
            value = f"{distance} cell(s)"
            color = RED if distance <= 2 else ORANGE

        draw_text(
            f"{label}: {value}",
            x,
            y + 49 + i * 21,
            color,
            small_font
        )



def draw_decision_log():
    """Display recent robot decisions in the control panel."""
    x = PANEL_X + 15
    y = 570

    draw_text(
        "ROBOT DECISION LOG",
        x,
        y,
        DARK_BLUE,
        title_font
    )

    for i, entry in enumerate(decision_log[-2:]):
        draw_text(
            entry[:32],
            x,
            y + 25 + i * 18,
            BLACK,
            small_font
        )




# ============================================================
# 11. LLM INPUT INTERFACE
# ============================================================

def draw_llm_interface():
    draw_text(
        "LLM COMMAND",
        PANEL_X + 15,
        665,
        DARK_BLUE,
        title_font
    )

    pygame.draw.rect(
        screen, WHITE, command_box, border_radius=5
    )

    border_color = BLUE if command_active else GRAY

    pygame.draw.rect(
        screen,
        border_color,
        command_box,
        2,
        border_radius=5
    )

    if command_input:
        visible_text = command_input[-30:]
        text_color = BLACK
    else:
        visible_text = "Type navigation command..."
        text_color = GRAY

    draw_text(
        visible_text,
        command_box.x + 7,
        command_box.y + 10,
        text_color,
        small_font
    )

    processing = (
        llm_future is not None and not llm_future.done()
    )

    draw_button(
        send_button,
        "PROCESSING..." if processing else "SEND COMMAND",
        GRAY if processing else GREEN
    )

    # Status text below the button.
    status = llm_status

    if len(status) > 35:
        draw_text(
            status[:35],
            PANEL_X + 15,
            630,
            DARK_BLUE,
            small_font
        )
        draw_text(
            status[35:70],
            PANEL_X + 15,
            650,
            DARK_BLUE,
            small_font
        )
    else:
        draw_text(
            status,
            PANEL_X + 15,
            635,
            DARK_BLUE,
            small_font
        )


# ============================================================
# 12. CONTROL PANEL
# ============================================================


def draw_panel():
    pygame.draw.rect(
        screen,
        LIGHT_GRAY,
        (PANEL_X, 0, PANEL_WIDTH, SCREEN_HEIGHT)
    )

    draw_text(
        "ROBOT CONTROL",
        PANEL_X + 15, 12,
        DARK_BLUE, title_font
    )

    draw_text(f"Position: {robot_pos}", PANEL_X + 15, 42)
    draw_text(f"Goal: {goal_pos}", PANEL_X + 15, 62, BLACK, small_font)

    draw_button(button_up, "UP", DARK_BLUE)
    draw_button(button_left, "LEFT", DARK_BLUE)
    draw_button(button_down, "DOWN", DARK_BLUE)
    draw_button(button_right, "RIGHT", DARK_BLUE)

    draw_button(button_auto, "AUTO PATH", GREEN)
    draw_button(button_stop, "STOP", RED)
    draw_button(button_reset, "RESET", BLUE)

    edit_label = "EDIT: ON" if edit_mode else "EDIT OBSTACLES"
    edit_color = ORANGE if edit_mode else DARK_BLUE
    draw_button(button_edit, edit_label, edit_color)

    draw_text("Status:", PANEL_X + 15, 343, DARK_BLUE)
    draw_text(message[:34], PANEL_X + 15, 363, BLACK, small_font)

    draw_sensor_readings()
    draw_decision_log()
    draw_llm_interface()


# ============================================================
# 13. MAIN GAME LOOP
# ============================================================

running = True

try:
    while running:
        clock.tick(60)

        # Check completed LLM requests without blocking Pygame.
        handle_llm_result()

        for event in pygame.event.get():

            if event.type == pygame.QUIT:
                running = False

            # ---------------- KEYBOARD ----------------

            elif event.type == pygame.KEYDOWN:

                if command_active:
                    if event.key == pygame.K_RETURN:
                        submit_llm_command()
                        command_active = False

                    elif event.key == pygame.K_BACKSPACE:
                        command_input = command_input[:-1]

                    elif event.key == pygame.K_ESCAPE:
                        command_active = False

                    elif event.unicode.isprintable():
                        if len(command_input) < 200:
                            command_input += event.unicode

                else:
                    if event.key == pygame.K_ESCAPE:
                        running = False

                    elif event.key == pygame.K_UP:
                        auto_running = False
                        move_robot((-1, 0))

                    elif event.key == pygame.K_DOWN:
                        auto_running = False
                        move_robot((1, 0))

                    elif event.key == pygame.K_LEFT:
                        auto_running = False
                        move_robot((0, -1))

                    elif event.key == pygame.K_RIGHT:
                        auto_running = False
                        move_robot((0, 1))

            # ---------------- MOUSE ----------------

            elif event.type == pygame.MOUSEBUTTONDOWN:

                mouse_pos = event.pos

                if event.button != 1:
                    continue

                if command_box.collidepoint(mouse_pos):
                    command_active = True

                elif send_button.collidepoint(mouse_pos):
                    command_active = False
                    submit_llm_command()

                elif edit_mode and (
                    AXIS_MARGIN <= mouse_pos[0]
                    < AXIS_MARGIN + COLS * CELL_SIZE
                    and AXIS_MARGIN <= mouse_pos[1]
                    < AXIS_MARGIN + ROWS * CELL_SIZE
                ):
                    command_active = False
                    toggle_obstacle_at_pixel(mouse_pos)

                elif button_up.collidepoint(mouse_pos):
                    command_active = False
                    auto_running = False
                    move_robot((-1, 0))

                elif button_down.collidepoint(mouse_pos):
                    command_active = False
                    auto_running = False
                    move_robot((1, 0))

                elif button_left.collidepoint(mouse_pos):
                    command_active = False
                    auto_running = False
                    move_robot((0, -1))

                elif button_right.collidepoint(mouse_pos):
                    command_active = False
                    auto_running = False
                    move_robot((0, 1))

                elif button_auto.collidepoint(mouse_pos):
                    command_active = False
                    start_auto_navigation()

                elif button_stop.collidepoint(mouse_pos):
                    command_active = False
                    auto_running = False
                    message = "Navigation stopped"

                elif button_reset.collidepoint(mouse_pos):
                    command_active = False
                    robot_pos = start_pos
                    auto_path = []
                    auto_running = False
                    known_obstacles.clear()
                    update_sensor_map()
                    edit_mode = False
                    command_input = ""
                    message = "Simulation reset"
                    llm_status = "Enter a navigation command"

                elif button_edit.collidepoint(mouse_pos):
                    command_active = False
                    edit_mode = not edit_mode

                    if edit_mode:
                        message = "Click grid to edit obstacles"
                    else:
                        message = "Obstacle editing disabled"

                else:
                    command_active = False

        # ====================================================
        # AUTOMATIC NAVIGATION
        # ====================================================

        current_time = pygame.time.get_ticks()

        if (
            auto_running
            and current_time - last_move_time >= MOVE_INTERVAL
        ):
            last_move_time = current_time

            if robot_pos == goal_pos:
                auto_running = False
                auto_path = []
                message = "Goal reached!"

            elif not auto_path:
                start_auto_navigation()

            else:
                next_pos = auto_path[0]

                # If the planned step is blocked in the real environment,
                # record it and replan using the robot's discovered map.
                if next_pos in obstacles:
                    known_obstacles.add(next_pos)
                    update_sensor_map()
                    message = "New obstacle discovered! Replanning..."

                    new_path = find_path(
                        robot_pos,
                        goal_pos,
                        known_obstacles,
                        ROWS,
                        COLS
                    )

                    if new_path is None:
                        auto_path = []
                        auto_running = False
                        message = "No alternative route available"
                    elif not new_path:
                        auto_path = []
                        auto_running = False
                        message = "Goal reached!"
                    else:
                        auto_path = new_path
                        message = "Route updated using discovered map"

                elif not (
                    0 <= next_pos[0] < ROWS
                    and 0 <= next_pos[1] < COLS
                ):
                    auto_running = False
                    auto_path = []
                    message = "Boundary detected"

                else:
                    robot_pos = next_pos
                    auto_path.pop(0)
                    update_sensor_map()

                    if robot_pos == goal_pos:
                        auto_running = False
                        auto_path = []
                        message = "Goal reached!"

        # ====================================================
        # RENDER
        # ====================================================

        screen.fill(WHITE)

        draw_grid()
        draw_panel()

        pygame.display.flip()

finally:
    executor.shutdown(wait=False, cancel_futures=True)
    pygame.quit()
    sys.exit()
