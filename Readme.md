Urban Swarm: "Bottleneck" & Homeostasis Update
1. Overview & Research Goal

This update transitions the simulation from a standard grid to a constrained topology to rigorously test the "Self-Organization" capabilities of the swarm.

As noted in the project research (Electronic Homeostasis Research), standard engineered systems are often "fragile to unmodeled conditions". The previous uniform 6x6 grid offered too many alternative routes, masking the agents' inability to handle critical congestion.

Key Changes:

    Topology Shift: Replaced the Manhattan Grid with a "Board Game" map (Two Zones + One Bridge).

    Observability: Implemented a real-time Homeostatic Health HUD to quantify system stability.

2. Architectural Changes
A. The "Bottleneck" Map (city.py)

We have abandoned the procedural grid generation for a hand-crafted irregular graph.

    Residential Zone (West): Dense node cluster (res-X-X).

    Commercial Zone (East): Dense node cluster (com-X-X).

    The Bridge: A single, high-cost connection between the zones.

    Why: This forces all inter-zone traffic into a single point of failure, creating the high-load conditions necessary to test if the "Traffic Penalty" logic effectively regulates flow.

B. Logic Engine & Metrics (logic_engine.py)

Added a calculate_metrics() method that runs every tick to assess the city's "vital signs."

    Metric 1: System Efficiency (%)

        Formula: Max Possible SpeedCurrent Average Speed​×100

        Meaning: Measures the impact of congestion. If efficiency drops below 40%, the system is effectively "ischemic" (deadlocked).

    Metric 2: System Entropy (Variance)

        Formula: Statistical variance of current_load across all road edges.

        Meaning: Measures the distribution of traffic.

            Low Entropy: Traffic is evenly spread (Good Self-Organization).

            High Entropy: Some roads are empty while others are jammed (Poor coordination/Bottlenecking).

C. Visualization (visualizer.py)

    HUD: Added a text overlay displaying Efficiency and Entropy in real-time.

    Visual Debug: The "Bridge" edges are rendered thicker and in a distinct color to visually isolate the bottleneck dynamics.

    Color Coding: The Efficiency text changes color (Green → Orange → Red) to indicate system health status.

3. How to Interpret the Simulation

When running the new build, watch for this specific behavioral loop:

    Phase 1 (Flow): Agents spawn and move freely. Efficiency is ~90%, Entropy is low.

    Phase 2 (The Crunch): Agents randomly select destinations in the opposite zone. They flock to the bridge.

    Phase 3 (Collapse):

        The bridge load spikes.

        Efficiency drops rapidly (as the traffic penalty formula slows bridge crossers to a crawl).

        Entropy spikes (variance between the jammed bridge and empty side streets).

    Phase 4 (Recovery?): This is the test. Does the system clear itself, or does it remain in a permanent jam? (Currently, without Adaptive AI, expect a permanent jam).

4. Setup & Run

No new dependencies are required.
Bash
