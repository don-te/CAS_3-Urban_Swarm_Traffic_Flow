import streamlit as st
import subprocess
import sys
import os

st.set_page_config(page_title="Traffic Automation", layout="centered")

st.title("Traffic Simulation Automation")
st.markdown("Configure the automation parameters and start the simulation.")

# Inputs
col1, col2 = st.columns(2)
with col1:
    iterations = st.number_input("Iterations per Position", min_value=1, value=5)
    pos_updates = st.number_input("Position Updates", min_value=1, value=2)

with col2:
    n_start = st.number_input("Start Agent Count", min_value=1, value=1)
    n_end = st.number_input("End Agent Count", min_value=1, value=10)
    step = st.number_input("Agent Step Size", min_value=1, value=2)

if st.button("Start Automation", type="primary"):
    st.info("Launching Simulation...")
    
    # Construct command
    cmd = [
        sys.executable, "automation_runner.py",
        "--iterations", str(iterations),
        "--pos_updates", str(pos_updates),
        "--n_start", str(n_start),
        "--n_end", str(n_end),
        "--step", str(step)
    ]
    
    # Run in subprocess
    try:
        # We use Popen to let it run independently
        subprocess.Popen(cmd, cwd=os.getcwd())
        st.success("Simulation started in a new window!")
    except Exception as e:
        st.error(f"Failed to start simulation: {e}")

st.divider()
st.caption("Running: " + sys.executable)
