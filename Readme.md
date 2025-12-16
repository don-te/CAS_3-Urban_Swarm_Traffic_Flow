# Urban Swarm: Electronic Homeostasis & Traffic Flow

> **A Multi-Agent Simulation of Complex Adaptive Systems in Urban Environments**

## 🔬 Project Overview
This project simulates urban traffic as a **Cyber-Physical System (CPS)** to explore the concepts of **Electronic Homeostasis** and **Self-Organization**. 

Unlike traditional traffic models that optimize for efficiency, this simulation treats the city as a biological organism. It investigates how a "healthy" global state (Homeostasis) can emerge—or collapse—based purely on the local, decentralized interactions of independent agents (Auto Rickshaws and Police).

**Core Research Question:** Can a decentralized swarm of "greedy" agents self-organize to maintain system equilibrium when faced with critical bottlenecks and regulatory pressure?

---

## 🚀 Key Features

### 1. The "Bottleneck" Topology
We moved away from a standard grid to a **constrained topology** to stress-test the system:
* **Residential Zone (West) & Commercial Zone (East):** Dense, highly connected clusters.
* **The Bridge:** A single, high-cost connection between zones. This acts as a "pressure valve" to force congestion and test the limits of the system's flow.

### 2. Intelligent Agents
* **Auto Rickshaws:** Agents driven by "Greed." They use A* pathfinding to hunt passengers and deliver them for profit. Their speed is dynamically penalized by local traffic density (Social Physics).
* **Police Units:** Regulatory agents that patrol the streets. They actively hunt and fine "speeding" agents (those moving efficiently on empty roads), introducing a negative feedback loop to the system.

### 3. Real-Time "Vital Signs"
The simulation calculates system health metrics every frame:
* **System Efficiency (%):** Compares current average speeds against theoretical maximums. A drop below 40% indicates "Ischemia" (Deadlock).
* **Entropy (Variance):** Measures the distribution of load. High entropy means the system is failing to self-organize (e.g., one jammed bridge vs. empty streets).

---

## 🛠️ Architecture

The codebase is modular, separating graph topology, agent logic, and visualization.

| Module | Description |
| :--- | :--- |
| **`main.py`** | Entry point. Manages the game loop, clock, and event handling. |
| **`city.py`** | Generates the `networkx` graph. Defines the "Board Game" map with residential/commercial zones and the bridge. |
| **`logic_engine.py`** | The "Brain." Handles spawning, agent updates, and calculates global metrics (Efficiency/Entropy). |
| **`rickshaw.py`** | Defines the Rickshaw agent, including passenger hunting and traffic-dependent movement physics. |
| **`police.py`** | Defines the Police agent, featuring a state machine for Patrol vs. Pursuit. |
| **`visualizer.py`** | `pygame` renderer. Draws the graph, agents, and the HUD overlay. |
| **`config.py`** | Central configuration for physics constants, colors, and simulation rules. |

---

## 💻 Installation & Usage

### Prerequisites
* Python 3.8+
* `pip`

### 1. Install Dependencies
```bash
pip install -r requirements.txt