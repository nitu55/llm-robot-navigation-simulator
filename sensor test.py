
from robot.sensors import VirtualSensors

sensors = VirtualSensors(rows=15, cols=20, max_range=5)

robot_position = (5, 5)

obstacles = {
    (5, 8),  # Three cells east
    (2, 5),  # Three cells north
}

readings = sensors.scan(robot_position, obstacles)

print("Robot position:", robot_position)
print("Sensor readings:")

for direction, distance in readings.items():
    print(f"{direction.capitalize()}: {distance}")
