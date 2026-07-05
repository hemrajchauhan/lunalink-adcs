=====================================================================
 LunaLink ADCS Simulator
 Project X, LunaLink Simulation Challenge
 Spacecraft Design: Fundamentals, SS 2026, TUM
 Author: Hemraj Chauhan
=====================================================================

Simulated subsystem: ADCS (Attitude Determination and Control System)
for the LunaLink relay spacecraft in a 500 x 36,000 km Molniya-type
orbit. Scenarios: B-dot magnetic detumbling and quaternion-PD sun
pointing with reaction wheels and magnetic desaturation, each over
4 full orbits (42.7 hours of simulated time).


1. REQUIREMENTS
---------------------------------------------------------------------
- Python 3.13 or newer
- Windows, Linux or macOS with OpenGL support (for the 3D view)
- Internet access once, to install the dependencies


2. HOW TO INSTALL DEPENDENCIES
---------------------------------------------------------------------
Option A: uv (RECOMMENDED)

uv installs the required Python version for you (it reads
.python-version / pyproject.toml), creates the virtual environment
and installs all dependencies in one step. No separate Python 3.13
install is needed.

Install uv once:

    Windows (PowerShell):
        powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
    Linux / macOS:
        curl -LsSf https://astral.sh/uv/install.sh | sh

Then, in the project folder (the folder with pyproject.toml):

    uv sync

That is all. Run the programs with "uv run" as shown in sections
3 and 4 below.

Option B: pip and requirements.txt

Requires Python 3.13 or newer already installed. Open a terminal in
the project folder (the folder that contains requirements.txt):

    python -m venv .venv

    Windows:        .venv\Scripts\activate
    Linux / macOS:  source .venv/bin/activate

    pip install -r requirements.txt
    pip install -e .

The second pip command installs the project itself so that the
"python -m lunalink...." commands below work from anywhere.


3. HOW TO RUN THE SIMULATION (headless, no GUI)
---------------------------------------------------------------------
Simulation script: src/lunalink/main_simulation.py

    with uv:   uv run python -m lunalink.main_simulation
    with pip:  python -m lunalink.main_simulation

This runs both scenarios (detumbling, then sun pointing) without any
GUI, prints the sizing results, momentum budget, disturbance ranking
and pointing budget to the terminal, and writes all plots as PNG
files into the folder:  output/
(detumble_*.png and sunpoint_*.png)


4. HOW TO RUN THE GUI
---------------------------------------------------------------------
GUI script: src/lunalink/main_gui.py (alias of src/lunalink/main.py)

    with uv:   uv run python -m lunalink.main_gui
    with pip:  python -m lunalink.main_gui

The window opens maximised with a 3D orbit view on the left and the
controls and plots on the right:

  - Mission tab:         pick a mission, see all its details, press
                         "Run ADCS Simulation"
  - ADCS Simulation tab: adjust spacecraft, actuator and scenario
                         parameters, then press "Run Simulation"
  - Plot tabs below:     angular velocity, pointing error, wheel
                         momentum, disturbance torques, total
                         momentum, momentum budget, pointing budget.
                         Each chart has a short interpretation
                         under it.


5. REPORT
---------------------------------------------------------------------
The report PDF is in the folder:  report/

The report source (LaTeX) is output/LunaLink_ADCS_Report.tex. It
references the PNG files in the same folder by name, so regenerating
the plots (step 3) and recompiling updates the report figures:

    cd output
    pdflatex LunaLink_ADCS_Report.tex
    pdflatex LunaLink_ADCS_Report.tex


6. TROUBLESHOOTING
---------------------------------------------------------------------
- Blank or crashing 3D view: update the graphics driver; the
  simulation and the plots work regardless of the 3D view.
- Qt platform plugin errors on Linux: install the system libraries
  libegl1, libxkbcommon0, libfontconfig1.
- A 4-orbit run simulates 42.7 hours and takes a few seconds; the
  GUI shows a wait cursor while it runs.
=====================================================================
