# LunaLink ADCS — Documentation

A tutorial-style guide to the physics, the code, and how to use the LunaLink
Attitude Determination and Control System (ADCS) simulator.

These documents follow the **LunaLink ADCS Mathematical Framework** (Project X,
SS 2026). Every equation referenced as *"Eq. N"* or *"Sec. N"* is from that
framework, and each chapter says **where in the code** it lives and **whether
our implementation matches** the framework.

## How to read this

Read in order — each chapter builds on the previous one, mirroring the order in
which the simulation evaluates things each time step.

| # | Document | What it covers |
|---|----------|----------------|
| — | [README](README.md) | This page: the big picture |
| 01 | [Architecture & data](01-architecture-and-data.md) | Folder layout, JSON data model, what is data vs code |
| 02 | [Orbit mechanics](02-orbit-mechanics.md) | Kepler propagation, position & velocity (Sec. 3) |
| 03 | [Attitude & kinematics](03-attitude-kinematics.md) | Quaternions, pointing error (Sec. 4) |
| 04 | [Rigid-body dynamics](04-rigid-body-dynamics.md) | Box inertia, Euler's equation (Sec. 5) |
| 05 | [Environment models](05-environment-models.md) | Sun, eclipse, geomagnetic field, atmosphere (Sec. 7) |
| 06 | [Disturbance torques](06-disturbance-torques.md) | Gravity gradient, SRP, magnetic, drag (Sec. 6) |
| 07 | [Actuators & control](07-actuators-and-control.md) | Wheel/torquer sizing, B-dot, PD, desaturation (Sec. 8–9) |
| 08 | [The simulation loop](08-simulation-loop.md) | How one time step ties it all together (Sec. 10) |
| 09 | [Verification](09-verification.md) | Framework ↔ code cross-check, hand-calc anchors, known approximations |
| 10 | [Tutorial: create a mission](10-tutorial-create-mission.md) | Add a satellite / orbit / mission — inputs vs computed |
| 11 | [Momentum budget & hierarchy](11-momentum-budget.md) | Cyclic vs secular momentum, wheel/torquer sizing, lecture cross-check |
| 12 | [J2 secular drift rates](12-j2-secular-rates.md) | RAAN/apsidal drift, the 63.4° critical inclination, justifying the fixed-orbit assumption |
| 13 | [Attitude determination](13-attitude-determination.md) | Gyro + star tracker, complementary filter, knowledge vs control error, the pointing budget |

## The simulation in one paragraph

The simulator answers: *"Given a spacecraft tumbling in a highly-elliptical
orbit, how does its attitude evolve under environmental disturbances and an
active control law?"* Each time step it (1) propagates the **orbit** to get
position and velocity, (2) evaluates the **environment** (Sun direction,
eclipse, magnetic field, air density) at that point, (3) computes the
**disturbance torques** acting on the body, (4) runs the active **control law**
(B-dot detumbling or quaternion-PD sun-pointing with reaction wheels),
(5) integrates the **rigid-body dynamics** and **attitude kinematics** with
RK4, and (6) logs everything for the plots. This is exactly the loop in
framework **Section 10**.

## The mission this models

LunaLink is a 500 kg relay spacecraft in a **Molniya-type HEO**
(perigee 500 km, apogee 36 000 km, inclination 63.4°). The 63.4° "critical
inclination" freezes the argument of perigee so apogee stays over the northern
hemisphere. See [02-orbit-mechanics](02-orbit-mechanics.md) for why the stated
"≈12 h" period and the "500 × 36 000 km" altitudes are slightly inconsistent
(we keep the altitudes → ≈10.7 h, and flag it).

## Running it

```bash
pip install -e .
python -m lunalink.main_gui          # interactive GUI
python -m lunalink.main_simulation   # headless: writes plots to output/
```
