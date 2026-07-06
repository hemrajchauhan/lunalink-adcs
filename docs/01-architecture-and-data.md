# 01 - Architecture & Data Model

## Folder layout

```
src/lunalink/
├── config.py                 GUI window sizes, visualization scaling, scene colours
├── main.py / main_gui.py     GUI entry points
├── main_simulation.py        headless entry point (writes plots, no GUI)
│
├── data/                     ←-- ALL tunable parameters live here (not in code)
│   ├── bodies.json           celestial bodies (Sun, planets, Moon)
│   ├── satellites.json       spacecraft: mass, dimensions, parent, orbit
│   ├── missions.json         runnable scenarios: satellite + simulation params
│   ├── simulation_defaults.json   default ADCS/solver parameters
│   └── mission_profile.json  fixed brief constants (ground station, downlink…)
│
├── simulation/
│   ├── objects.py            dataclasses: OrbitElements, CelestialBody, Satellite, Mission
│   ├── defaults.py           JSON loaders (simulation defaults, mission profile)
│   ├── parameters.py         ADCSParams (a pure container - NO hard-coded numbers)
│   ├── simulator.py          simulate(): the RK4 integration loop
│   ├── system.py             SolarSystem: resolves every body's position vs time
│   ├── repositories/         read/write the JSON files (Body/Satellite/Mission)
│   └── physics/              ←-- one folder per group of equations
│       ├── constants.py      physical constants (GM, R_E, J2, Φ, c, M_B …)
│       ├── orbit/            kepler.py · propagation.py · builders.py
│       ├── attitude/         quaternion.py · pointing.py
│       ├── environment/      sun.py · eclipse.py · geomagnetic.py · atmosphere.py
│       ├── disturbances/     gravity_gradient.py · solar_radiation.py · magnetic.py · aerodynamic.py
│       ├── dynamics/         mass_properties.py · rigid_body.py
│       ├── actuators/        sizing.py
│       └── control/          detumble.py · pointing.py · desaturation.py
│
└── gui/                      PyQt6 + PyVista interface (tabs, 3D scene, plots)
```

## Three kinds of "numbers", three homes

The project deliberately separates *what kind* of value something is:

| Kind | Example | Lives in | Why |
|------|---------|----------|-----|
| **Physical constants** | `GM_EARTH`, speed of light, geomagnetic dipole | `physics/constants.py` | Universal - never change, single source of truth |
| **Mission/spacecraft/sim parameters** | mass, orbit, tumble rate, wheel capacity | `data/*.json` | Tunable per scenario - edited without touching code |
| **Display / GUI settings** | window size, scene colours, planet scaling | `config.py` | Presentation only, no effect on physics |

`ADCSParams` (in `parameters.py`) is a *container only*: every field defaults to
`None` and is filled from JSON. There are no tuning magic numbers in the
simulation code.

## The data objects (`simulation/objects.py`)

- **`OrbitElements`** - the six classical Keplerian elements:
  `semi_major_axis_m, eccentricity, inclination_deg, raan_deg,
  arg_periapsis_deg, mean_anomaly_epoch_deg`.
- **`CelestialBody`** - `name, color, radius_m, axial_tilt_deg,
  rotation_period_h, has_ring, parent, orbit`.
- **`Satellite`** - `name, color, mass_kg, dimensions_m (L,W,H), parent, orbit`.
- **`Mission`** - `name, satellite, description, simulation` (a dict of parameter
  overrides on top of `simulation_defaults.json`).

## How the layers talk

```
data/*.json ──> repositories ──> objects (dataclasses)
                                     │
   simulation_defaults.json ─────────┤
                                     ▼
                       parameters.ADCSParams.from_mission(satellite, sim_params)
                                     ▼
                          simulator.simulate(params)  ──> result dict ──> plots
                                     ▲
                       physics/*  (orbit, attitude, environment,
                                   disturbances, dynamics, control)
```

`SolarSystem` (`system.py`) is a parallel consumer of the same body/satellite
data, used by the 3D view to place everything in space over time.

Next: [02 - Orbit mechanics](02-orbit-mechanics.md).
