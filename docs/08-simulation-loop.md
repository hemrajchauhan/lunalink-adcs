# 08 - The Simulation Loop (Framework Sec. 10)

This is where everything from chapters 02–07 comes together. One function -
`simulator.simulate(params)` - runs the whole thing.

**Code:** `simulation/simulator.py`

## State and inputs

```
state x = [ q (4),  ω (3),  h_w (3) ]
```

`params` is an `ADCSParams` built from a satellite (mass, dimensions, orbit) and
a mission's simulation parameters (mode, actuators, gains, solver constants) -
all sourced from JSON (see [10-tutorial](10-tutorial-create-mission.md)).

## Setup (before the loop)

1. `I = box_inertia(mass, dims)` (Eq. 16).
2. `period = 2π√(a³/μ)`, total time = `n_orbits · period`, step count = `total/dt`.
3. PD gains `K_p, K_d` from `ω_n, ζ` (Eq. 36).
4. Auto-size the B-dot gain to saturate the torquers near perigee.
5. Initial state per `mode` (a tumble for detumble; near-Sun-pointed for
   sun-pointing).

## Each time step (the framework's 6-step recipe, Sec. 10)

```
1. Orbit:    r, v = state_vectors(elements, μ, t)              (Eq. 5–6)
             Sun ŝ (Eq. 25);  eclipse flag (Eq. 26);
             field B (Eq. 27);  density ρ (Eq. 28)
2. Rotate r, ŝ, B into body axes via R(q)                      (Eq. 12)
3. Disturbances: T_gg + T_srp + T_mag + T_aero                 (Eq. 19–22)
4. Control:  B-dot (Eq. 33)  OR  PD (Eq. 35) + desat (Eq. 37); torque clipped
             to the wheel limit, ḣ_w limited so |h_w| stays within capacity
5. Dynamics:  ω̇ (Eq. 18);  kinematics q̇ (Eq. 13);  wheels ḣ_w
6. Integrate (RK4), re-normalise q, advance h_w with the same limited ḣ_w
   (momentum only ever leaves the wheels through the magnetic desat torque)
```

The control torque and disturbances are held constant across the four RK4
stages (they vary slowly relative to `dt`); only the gyroscopic term and `q̇`
use the stage state. This is stable and fast.

## Time step `dt`

Default `dt = 8 s` (from JSON), roughly 10 s wall-clock for the default
4 orbits. The framework
allows 1–5 s for the slow modes and ≤0.5 s through perigee; because the orbit is
**analytic** (Kepler each step, no integration error in position) an 8 s step
resolves the attitude dynamics well. Lower `dt_s` in `simulation_defaults.json`
or a mission for higher fidelity.

## Outputs (the `result` dict → plots)

| Key | Plot | Meaning |
|-----|------|---------|
| `omega_deg_s`, `omega_mag_deg_s` | Angular Velocity | detumbling convergence |
| `attitude_error_deg` | Attitude Error | sun-pointing accuracy |
| `wheel_momentum_mag_nms` | Reaction-Wheel Momentum | build-up + desaturation saw-tooth |
| `T_gg/srp/mag/aero_nm`, `disturbance_nm` | Disturbance Torque | torque vs orbit position |
| `angular_momentum_nms` | Angular Momentum | `‖H‖` integrator check |
| `euler_deg`, `radius_km`, `eclipse`, `t_acquire_h`, `period_h` | - | reporting |

## GUI vs headless

- **GUI:** the ADCS/Mission tab builds `params` and emits them; the controller
  runs `simulate()` and pushes the result to the plot tabs (only on **Run**,
  never on startup).
- **Headless:** `python -m lunalink.main_simulation` runs a mission and writes
  PNGs to `output/` - the "must run headless" deliverable.

Next: [09 - Verification](09-verification.md).
