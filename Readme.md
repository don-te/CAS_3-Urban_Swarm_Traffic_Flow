# Self-Organization in Multi-Agent Systems

## 🚦 Project Overview
This project simulates **Self-Organization in Urban Traffic** modeled as a **Complex Adaptive System (CAS)**. It simulates autonomous agents navigating a city grid using local decision-making rules. Unlike traditional navigation systems that rely solely on static shortest-path algorithms (like Dijkstra or A* on empty roads), this system integrates **emergent behavior analysis** and **evolutionary learning** to find optimal paths in dynamic, high-density environments.

The agents in this system are generic and configurable; they can represent any type of entity (autonomous pods, cars, delivery drones, etc.) based on their initialized properties such as speed factors and size.

## 🧠 Conceptual Framework

### 1. From Individual Agents to Complex Systems
The core philosophy of this simulation is **Self-Organization**.
* **The Agent:** A single entity with simple local rules: "Go to target," "Maintain separation," "Reverse if stuck."
* **The Swarm:** As the number of agents ($N$) increases, the system transitions from simple linear interactions to a **Complex Adaptive System**.
* **Emergence:** Traffic patterns, lane formation, congestion waves, and gridlocks are not explicitly programmed. They **emerge** from the collective interactions of hundreds of agents competing for space and resources.

### 2. The Problem with "Shortest Path"
Traditional navigation (e.g., standard GPS routing) often routes all users via the mathematically shortest distance.
* **The Flaw:** If 100 agents all take the "shortest" road, that road becomes the "slowest" due to congestion (Braess's Paradox).
* **Our Solution:** This system implements an evolutionary feedback loop. Agents "learn" from previous iterations. If the shortest path resulted in a collision or high delay, the agent marks that path as "forbidden" and explores alternative, longer—but faster—routes in the next generation.

---

## 🤖 Agent Architecture & Intelligence

The agent (implemented in `src/entities/rickshaw.py`) is designed as a generic autonomous entity defined by its initialization properties.

### Configurable Properties
The behavior of an agent is determined by parameters set during instantiation:
* **`speed_factor`**: Determines if the agent acts like a fast vehicle (e.g., car) or a slow vehicle (e.g., truck/cargo).
* **`dest_type`**: Agents can target specific coordinate nodes or dynamic edges.
* **`immunity_timer`**: Defines resilience after collisions.

### Core Components
* **Navigator:** Uses a modified NetworkX pathfinding engine that accounts for `forbidden_paths` (memory of past failures).
* **Collision Detection:** A physics-based boundary check using Haversine distance.
* **Reversing Logic:** A state machine that detects gridlocks (velocity $\approx$ 0 for $t$ seconds) and triggers a reverse maneuver to unclog intersections.

### The "Learning" Model (Evolutionary Optimization)
Instead of a heavy Neural Network, we use an **Evolutionary Strategy** optimized for swarm logic (located in `src/core/scenario.py`):

1.  **Generation 1:** Agents use naive Dijkstra (Shortest Distance).
2.  **Evaluation:** At the end of the trip, the system evaluates:
    * Did the agent collide? $\rightarrow$ **Punishment**: Add route to `forbidden_paths`.
    * Did the agent arrive efficiently? $\rightarrow$ **Reward**: Lock this route as `forced_path` for the next run.
3.  **Generation N+1:** Agents with "forced paths" repeat their success. Agents who failed are forced to explore suboptimal edges, effectively distributing the traffic load across the network and self-organizing the flow.

---

## 📐 Mathematical Models

### 1. Traffic Penalty Model
Speed is not constant; it is a function of edge density. As more agents enter an edge ($u, v$), the traversal cost increases.

$$Speed_{actual} = \frac{Speed_{base} \times SpeedFactor}{1 + (Load_{current} \times PenaltyConstant)}$$

* $Load_{current}$: Number of agents currently on the edge.
* $PenaltyConstant$: A tuning parameter defining how quickly traffic slows down.

### 2. Collision Detection (Haversine Formula)
Since the simulation uses real-world lat/lon coordinates, we use the Haversine formula to calculate the great-circle distance between two agents ($P_1, P_2$).

$$a = \sin^2\left(\frac{\Delta\phi}{2}\right) + \cos \phi_1 \cdot \cos \phi_2 \cdot \sin^2\left(\frac{\Delta\lambda}{2}\right)$$
$$c = 2 \cdot \text{atan2}(\sqrt{a}, \sqrt{1-a})$$
$$d = R \cdot c$$

* $\phi$: Latitude (radians), $\lambda$: Longitude (radians).
* $R$: Earth's radius ($6,371,000$ meters).
* **Collision Condition:** If $d < \text{AgentSize} \text{ meters}$.

### 3. Visual Orientation
To render the agent facing the correct direction on the screen:

$$\theta = \text{atan2}(-(y_2 - y_1), (x_2 - x_1))$$

* *Note:* If `reversing == True`, $\theta = \theta + \pi$.

---

## 📂 Project Structure

```text
CAS_3-Urban_Swarm_Traffic_Flow/
├── main.py                  # Entry point for the GUI Visualizer
├── automation_runner.py     # Headless script for data collection/training
├── automation_gui.py        # Streamlit dashboard to control automation
├── simulation_data.csv      # Output logs (Traffic & Collision stats)
├── requirements.txt         # Dependencies
└── src/
    ├── config.py            # Global simulation constants (FPS, Colors, Physics)
    ├── core/
    │   ├── engine.py        # Main physics loop and state management
    │   ├── scenario.py      # Evolutionary logic & Scenario loading/saving
    │   └── collision.py     # N^2 Collision detection system
    ├── entities/
    │   ├── rickshaw.py      # Generic Agent logic and state machine
    │   └── navigator.py     # Pathfinding (NetworkX wrapper)
    ├── ui/
    │   ├── visualizer.py    # Pygame rendering engine
    │   └── interface.py     # UI components (Buttons, Sliders)
    ├── utils/
    │   ├── data_logger.py   # CSV Logging utility
    │   └── math_utils.py    # Haversine & Screen mapping math
    └── world/
        └── city.py          # Graph generation (Manhattan Grid)
```
---
## 📦 Installation

### Prerequisites
* Python 3.8 or higher
* pip (Python package installer)

### Setup Steps
1.  **Clone the Repository**
    ```bash
    git clone <repository-url>
    cd CAS_3-Urban_Swarm_Traffic_Flow
    ```

2.  **Install Dependencies**
    The project relies on `pygame` for visualization, `networkx` for graph logic, and `streamlit` for the automation dashboard.
    ```bash
    pip install -r requirements.txt
    ```
    *Core libraries installed:* `networkx`, `pydeck`, `pandas`, `streamlit`, `pygame`.

---

## 🛠 Usage Guide

### 1. Visual Simulation (GUI)
Run the main visualizer to watch the swarm emergence in real-time.
```bash
python main.py
