# LLM-Powered Robot Navigation Simulator 🤖

A software-based robot navigation simulator built with **Python, Pygame, A* path planning, virtual sensors, and a Large Language Model (LLM)**. The project simulates a robot navigating a grid-based environment, detecting obstacles through virtual sensors, and planning routes toward a goal.

## 🚀 Features

- **Interactive 2D simulation:** Visualize a robot, goal, grid, and obstacles using Pygame.
- **A* path planning:** Calculate routes around known obstacles using the A* search algorithm.
- **Virtual sensors:** Simulate directional distance sensing in the north, south, east, and west directions.
- **Automatic navigation:** Let the robot follow a calculated path toward its goal.
- **Obstacle editing:** Modify the environment by adding or removing obstacles.
- **Obstacle-aware replanning:** Recalculate a route when an obstacle blocks the robot's planned movement.
- **LLM-powered commands:** Interpret natural-language navigation commands using NVIDIA's Nemotron model.
- **Decision log:** Display recent navigation events in the control panel.
- **Manual control:** Move the robot using on-screen controls.

## 🛠️ Technologies Used

- Python
- Pygame
- NumPy
- Matplotlib
- A* search algorithm
- NVIDIA Nemotron via LangChain
- python-dotenv

## 📁 Project Structure

```text
robo_simulator/
├── main.py
├── llm_controller.py
├── requirements.txt
├── .env.example
├── navigation/
│   ├── __init__.py
│   └── astar.py
└── robot/
    ├── __init__.py
    └── sensors.py
```

## ⚙️ Installation and Setup

### 1. Clone the repository

```bash
git clone https://github.com/YOUR-USERNAME/llm-robot-navigation-simulator.git
cd llm-robot-navigation-simulator
```

### 2. Create a virtual environment

```bash
python -m venv .venv
```

Activate it on Windows PowerShell:

```powershell
.\.venv\Scripts\Activate.ps1
```

### 3. Install dependencies

```bash
python -m pip install -r requirements.txt
```

### 4. Configure the NVIDIA API key

Create a `.env` file in the project root:

```text
NVIDIA_API_KEY=your_nvidia_api_key_here
```

Replace the placeholder with your own NVIDIA API key. Never commit your real `.env` file or expose your API key publicly.

### 5. Run the simulator

```bash
python main.py
```

## 🎮 How to Use

- Use the directional controls to move the robot manually.
- Use **AUTO PATH** to calculate and follow a route to the goal.
- Use **STOP** to stop automatic navigation.
- Use **RESET** to reset the simulation.
- Use **EDIT OBSTACLES** to modify the grid environment.
- Enter a natural-language navigation command in the LLM command panel and press **SEND COMMAND**.
- Observe the sensor rays, sensor readings, robot position, and decision log.

## 🧠 How It Works

1. The environment is represented as a discrete grid containing a robot, a goal, and obstacles.
2. Virtual sensors simulate distance measurements in four cardinal directions.
3. The A* algorithm searches for a path using movement costs and a heuristic.
4. The robot can move manually or follow a planned route automatically.
5. If an obstacle blocks the next movement, the navigation logic can update its map and attempt to replan.
6. The LLM interprets natural-language commands and converts them into structured navigation instructions.

## ⚠️ Limitations

- This is a software simulation; no physical robot or hardware sensors are used.
- Sensor readings and sensor rays are simulated.
- The environment uses a discrete grid rather than continuous physical space.
- The simulation has access to the environment's obstacle information for collision checking; it is not a fully autonomous perception system.
- LLM command interpretation depends on API availability and model responses.

## 🔮 Future Improvements

- More realistic sensor and robot-motion models.
- Improved partial-observation mapping.
- Additional path-planning algorithms.
- More robust LLM command handling and error recovery.
- Simulation metrics for path length, planning time, and navigation success.

## 👨‍💻 Author

**Nitish Kumar**

Electrical Engineering Student | Interested in Robotics, Artificial Intelligence, and Quantum Computing

## 📄 License

A license can be added to this project when you decide how others may use, modify, and distribute the code.