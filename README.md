# LunaLink ADCS Simulator

Attitude Determination and Control System (ADCS) simulator for **LunaLink**,
a 500 kg relay spacecraft in a Molniya-type highly elliptical Earth orbit
(500 km perigee, 36,000 km apogee, 63.4° inclination).

The simulator propagates the orbit analytically, models the space environment
(Sun, eclipse, geomagnetic field, atmosphere), computes the four classical
disturbance torques, runs the active control law (B-dot detumbling,
quaternion-PD sun pointing with reaction wheels, magnetic desaturation, or a
rest-to-rest slew) and integrates the rigid-body attitude dynamics with RK4.
A gyro + star-tracker complementary filter runs in parallel to split the
pointing budget into knowledge and control error.

A PyQt6 GUI shows a 3D solar-system view, mission management and all result
plots; a headless entry point produces the same plots as PNG files.

## Requirements

- **Python 3.13 or newer** (see `.python-version`)
- Windows, Linux or macOS with OpenGL support (for the 3D view)
- Dependencies (installed automatically): numpy, scipy, matplotlib,
  PyQt6, pyqtgraph, pyvista, pyvistaqt

## Installation

### Option A: with pip and requirements.txt

```bash
git clone <repository-url>
cd lunalink-adcs
python -m venv .venv

# Windows
.venv\Scripts\activate
# Linux / macOS
source .venv/bin/activate

pip install -r requirements.txt
pip install -e .
```

### Option B: with uv (recommended)

[uv](https://docs.astral.sh/uv/) is a fast Python package manager that reads
`pyproject.toml`, installs the right Python version and manages the virtual
environment for you.

Install uv once:

```bash
# Windows (PowerShell)
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"

# Linux / macOS
curl -LsSf https://astral.sh/uv/install.sh | sh
```

Then set up and run the project:

```bash
git clone <repository-url>
cd lunalink-adcs
uv sync
```

## Running

### Interactive GUI

```bash
uv run python -m lunalink.main        # with uv
python -m lunalink.main               # with an activated venv
```

`python -m lunalink.main_gui` is an equivalent alias kept for the brief's
naming convention.

Workflow inside the GUI:

1. **Mission tab**: pick a mission (details are shown on the left) and press
   "Run ADCS Simulation", or
2. **ADCS Simulation tab**: fine-tune spacecraft, actuator and scenario
   parameters, then press "Run Simulation".
3. Inspect the result tabs below: Angular Velocity, Pointing Error, Wheel
   Momentum, Disturbance Torques, Total Momentum, Momentum Budget and
   Pointing Budget. Each chart has a short interpretation underneath.
4. **Visualization tab** controls the 3D playback speed; the **Objects tab**
   lets you add/edit celestial bodies and satellites.

### Headless (no GUI)

Runs the two scenarios required by the project brief, each over 4 full orbits
(about 43 h of simulated time, satisfying "at least 3 full orbits / at least
36 hours"): B-dot magnetic detumbling from a 10°/s tumble, then quaternion-PD
sun pointing with reaction wheels and magnetic desaturation. All plots are
written as PNG files to `output/` (`detumble_*.png` and `sunpoint_*.png`) and
a full numeric report is printed (actuator sizing, momentum budget,
disturbance hierarchy, J2 drift, pointing budget):

```bash
uv run python -m lunalink.main_simulation
python -m lunalink.main_simulation
```

Reference plots for the default configuration live in `output/`, next to the
report source `output/LunaLink_ADCS_Report.tex`. The LaTeX file references
the PNG files by name, so regenerating the plots updates the report on the
next compile:

```bash
cd output
pdflatex LunaLink_ADCS_Report.tex
pdflatex LunaLink_ADCS_Report.tex   # second pass resolves references
```

## Project layout

```
src/lunalink/
├── config.py              GUI window and 3D display-scaling constants
├── main.py                GUI entry point
├── main_simulation.py     headless entry point (plots to output/)
├── data/                  all mission/spacecraft/simulation parameters (JSON)
├── gui/
│   ├── theme.py           application-wide dark stylesheet
│   ├── main_window.py     3D scene | controls + plots layout
│   ├── views/             control tabs, plot tabs (plot_tabs/style.py holds
│   │                      the shared chart theme), mission info panel
│   ├── dialogs/           add-mission and add-object dialogs
│   └── visualization/     PyVista 3D scene, camera, display transforms
└── simulation/
    ├── simulator.py       the ADCS time-stepping loop (RK4)
    ├── analysis.py        momentum budget, disturbance hierarchy
    ├── parameters.py      typed parameter container (values come from JSON)
    ├── repositories/      JSON persistence for bodies/satellites/missions
    └── physics/           orbit, attitude, dynamics, environment,
                           disturbances, control, determination, actuators
```

All tunable numbers live in `src/lunalink/data/*.json`; the physics modules
contain no magic constants.

## Documentation

`docs/` is a chapter-by-chapter guide that maps every implemented equation to
the code and to the mission framework, including verification anchors:
start at [docs/README.md](docs/README.md).

## Troubleshooting

- **Blank or crashing 3D view**: update your graphics drivers; the PyVista
  view needs working OpenGL. The simulation and plots run fine regardless.
- **Qt platform plugin errors on Linux**: install the system Qt/X11 libraries
  (`libegl1`, `libxkbcommon0`, `libfontconfig1`).
- **Slow first run**: a 4-orbit run propagates about 43 hours of simulated
  time and takes several seconds; the GUI shows a wait cursor meanwhile.
