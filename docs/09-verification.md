# 09 — Verification: Framework ↔ Code

This is the "did we implement it correctly?" chapter. It maps **every** equation
in the framework to the code that implements it, lists the hand-calc anchors we
reproduce, and is honest about the deliberate approximations.

## Equation map (framework Sec. 11, extended)

| Framework | Eq. | Implemented in | Status |
|-----------|-----|----------------|--------|
| Momentum / Euler (19‑1,2) | 17 | `physics/dynamics/rigid_body.py` | ✅ |
| EoM expansion (19‑3,4) | 18 | `rigid_body.state_derivative` | ✅ |
| Gyroscopic torque (19‑13) | 17 | `rigid_body.state_derivative` (`ω×(Iω+h_w)`) | ✅ |
| Orbit rate (19‑14) | 7 | `orbit/kepler.mean_motion` | ✅ |
| Kepler propagation | 3–6 | `orbit/kepler.py`, `orbit/propagation.py` | ✅ |
| Box inertia | 16 | `dynamics/mass_properties.box_inertia` | ✅ |
| Quaternion kinematics | 12–13 | `attitude/quaternion.py` | ✅ |
| Euler angles (report) | 14 | `attitude/pointing.quat_to_euler321` | ✅ |
| Pointing-error metric | 15 | `attitude/pointing.pointing_error_deg` | ✅ |
| Sun ephemeris | 23–25 | `environment/sun.py` | ✅ |
| Eclipse | 26 | `environment/eclipse.py` | ✅ |
| Geomagnetic dipole (vector) | 27 | `environment/geomagnetic.py` | ✅ (aligned dipole) |
| Atmospheric density | 28 | `environment/atmosphere.py` | ✅ |
| Gravity gradient (19‑8) | 19 | `disturbances/gravity_gradient.py` | ✅ |
| Solar pressure (19‑5) | 20 | `disturbances/solar_radiation.py` | ✅ (effective-area) |
| Magnetic (19‑7) | 21 | `disturbances/magnetic.py` | ✅ |
| Aero drag (19‑6) | 22 | `disturbances/aerodynamic.py` | ✅ |
| Slew / storage sizing | 29–30 | `actuators/sizing.py` | ✅ |
| Magnetorquer sizing (19‑17) | 31 | `actuators/sizing.magnetorquer_dipole` | ✅ |
| B-dot detumble (19‑15..17) | 33–34 | `control/detumble.py` | ✅ (ω×B variant) |
| PD pointing (19‑9,10) | 35–36 | `control/pointing.py` | ✅ |
| Desaturation | 37 | `control/desaturation.py` | ✅ |
| Critical inclination J2 | 9 | — | ⚠️ noted, not propagated |
| Nutation frequency | 38 | — | ⚠️ implicit (sets `dt`), not output |
| Integration loop | Sec. 10 | `simulation/simulator.py` | ✅ |

## Hand-calc anchors reproduced

These are the framework's "shaded box" numbers; the code reproduces them:

| Quantity | Framework | Code | 
|----------|-----------|------|
| Inertia Ix,Iy,Iz | 135, 208, 260 kg·m² | 135.4, 208.3, 260.4 |
| Semi-major axis / e | 24 628 km / 0.721 | 24 628 km / 0.7207 |
| Period | ≈10.7 h | 10.68 h |
| Perigee / apogee speed | 9.99 / 1.62 km/s | 9.99 / 1.62 km/s |
| Gravity gradient (perigee) | ~2.3×10⁻⁴ N·m | 2.29×10⁻⁴ |
| Magnetic torque (perigee, D=1) | ~5×10⁻⁵ N·m | 4.5×10⁻⁵ |
| Recommended wheel h_max | 3–5 N·m·s | ~4.1 N·m·s |
| Planet periods (Mercury…Neptune) | 0.24 … 164.8 yr | match |
| Moon period | 27.3 d | 27.45 d |
| `‖H‖` conservation (no torque) | flat | 0.03 %/orbit |

## Deliberate approximations (state these in a report)

1. **Period 10.7 h vs brief's 12 h** — kept the 500×36 000 km altitudes; flagged.
2. **J2 secular drift not propagated** — justified by the 63.4° critical
   inclination (Eq. 9 ⇒ ω̇_peri ≈ 0).
3. **Aligned magnetic dipole** `m̂ = −ẑ` (tilted/IGRF optional).
4. **SRP effective-area** model rather than per-face summation.
5. **B-dot uses `m = k(ω×B)`** (the standard ω×B form of `m = −k Ḃ`).
6. **Sun stationary; planet phasing approximate** (no full ephemeris) — affects
   the 3D view only, not the ADCS physics.
7. **3D visual scaling is non-physical** (planets/orbits scaled for visibility);
   all real values are in SI in the data and the simulation.

## How to re-run the checks yourself

`python -m lunalink.main_simulation` prints acquisition time and writes the
plots; compare the perigee/apogee disturbance magnitudes and the inertia
against the table above. The `physics/*` functions are pure and unit-testable in
isolation (e.g. `box_inertia(500,(2,1.5,1))` → `[135.4, 208.3, 260.4]`).

Next: [10 — Tutorial: create a mission](10-tutorial-create-mission.md).
