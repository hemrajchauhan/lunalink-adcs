# 11 — The Momentum Budget & Disturbance Hierarchy

This chapter explains the two numbers that drive ADCS hardware sizing — and a
result where LunaLink behaves **differently** from the textbook circular-orbit
case (TUM "The Pointing Problem" lecture, Part 3).

**Code:** `simulation/analysis.py` (computed in `simulation/simulator.py`,
shown in the GUI "Momentum Budget" tab and printed by `main_simulation`).

## The idea: integrate the torques

Each disturbance torque deposits angular momentum on the spacecraft. Read
`T = dH/dt` backwards: the momentum collected is the **area under the
torque–time curve**. We integrate the disturbance torque (body frame) into a
**disturbance angular-momentum demand**:

```
H_dist(t) = ∫₀ᵗ T_dist dt          (N·m·s, body frame)
```

Two features of `H_dist(t)` set the hardware (lecture slides 28–29):

| Behaviour | What it looks like | Sizes… | Hardware |
|-----------|--------------------|--------|----------|
| **Cyclic** | wiggles, returns to ~0 each orbit | how much must be **stored** | reaction wheels |
| **Secular** | climbs and never comes back | how much must be **removed** | magnetorquers |

A cyclic torque is *borrowed and returned* every orbit; a secular torque is a
*dripping tap* that fills the bucket forever.

## How we separate them (the robust bit)

A cyclic torque integrates to **exactly zero over a complete orbit**. So we
measure the **secular** part as the net momentum over an integer number of
orbits (the cyclic part cancels), and the **cyclic** part as the peak excursion
about that secular trend:

```
secular_per_orbit = (H at orbit N) − (H at orbit 0)) / N      # cyclic cancels
cyclic_swing      = max |H(t) − secular_trend(t)|              # the ± amplitude
```

`simulation/analysis.py → _secular_and_cyclic()`. (A naïve straight-line fit
over a non-integer number of cycles leaks the cyclic part into the secular
estimate — using complete orbits avoids that. Verified against a synthetic
case to the digit.)

## Sizing outputs

```
wheels   h_max   ≳ 1.5 × max( cyclic_swing , slew_demand )      # store
torquers dipole  ≳ secular_torque / B_perigee                   # dump (lower bound, T ⟂ B)
```

The wheel must cover the **larger** of the cyclic disturbance swing and the
**slew** demand (a 90° reorientation), per framework Sec. 8.

## LunaLink result (from an actual run)

`python -m lunalink.main_simulation` / the **Momentum Budget** tab:

```
Cyclic disturbance swing / orbit (store): ±0.131 N·m·s
Slew demand (90°):                         2.73  N·m·s   [slew-driven]
Secular momentum / day (dump):             0.236 N·m·s/day   (dipole ≳ 0.1 A·m²)
→ recommended wheel h_max:                 4.09  N·m·s

DISTURBANCE HIERARCHY        peak       perigee     apogee    behaviour
  Gravity gradient        1.56e-04    6.33e-05    4.28e-07     mixed
  Magnetic                4.46e-05    3.95e-05    1.89e-07     mixed
  Aerodynamic             7.30e-06    6.37e-06    0.00e+00     mixed
  Solar pressure          2.04e-06    2.04e-06    2.04e-06     secular
```

## Two findings worth putting in the report

**1. LunaLink is slew-driven, not storage-driven.** In the lecture, AI1's huge
600 m² array gives a **±97 N·m·s** cyclic swing that dwarfs everything — its
wheels are sized by *storage*. LunaLink is a small 500 kg box, so its
disturbance swing is only **±0.13 N·m·s**; the wheel size (≈4 N·m·s) is set by
the **90° slew**, not by disturbances. Same equations, opposite driver — a good
illustration that the *numbers*, not the formulas, decide the architecture.

**2. Eccentricity changes the secular/cyclic split.** The lecture's "gravity
gradient is cyclic, SRP is secular" is exact for a **circular** orbit, where GG
averages to zero each orbit. LunaLink's **e = 0.72** Molniya orbit concentrates
GG (and magnetic, aero) into a sharp **1/R³ perigee spike** (perigee 6.3×10⁻⁵
vs apogee 4.3×10⁻⁷ N·m) with no cancelling kick at apogee — so those torques are
classified **mixed** (part cyclic, part secular). Only **SRP** is purely
secular (constant in the Sun-fixed body frame). Our vector model captures this
eccentric-orbit behaviour that the circular-case scalar formulas do not.

## Cross-check vs the lecture

| Concept (lecture) | LunaLink implementation | Match |
|-------------------|-------------------------|-------|
| `H = ∫T dt`, area under curve | `H_dist(t)` accumulated in `simulator.py` | ✅ |
| Cyclic swing → storage (wheels) | `cyclic_swing_nms` → wheel `h_max` | ✅ |
| Secular/day → dump (torquers) | `secular_per_day_nms`, `dump_dipole_am2 = T/B` | ✅ |
| SRP secular ("patient enemy") | SRP classified **secular** | ✅ |
| GG cyclic (circular orbit) | GG **mixed** on the eccentric HEO | ✅ (eccentric refinement) |
| Size wheels for max(slew, storage) | `1.5 × max(cyclic, slew)` ≈ 4 N·m·s | ✅ |

Back to the [README index](README.md) · see also
[06 — Disturbance torques](06-disturbance-torques.md) and
[07 — Actuators & control](07-actuators-and-control.md).
