# 10 - Tutorial: Create a Satellite, Orbit & Mission

A practical guide to setting up your own scenario. There are two ways to do
everything: the **GUI** (Objects tab → right-click → Add; Mission tab → Add
Mission) or by **editing the JSON** files directly. Both end up in the same
`data/*.json` files.

The golden rule: **you provide the physical description; the code computes
everything derived from it.**

---

## A. Add a celestial body (planet / moon)

**File:** `data/bodies.json` · **GUI:** Objects tab → right-click *Celestial
Bodies* → *Add Celestial Body…*

| Parameter | You provide | Units | Computed for you |
|-----------|:-----------:|-------|------------------|
| name, color | ✅ | - | |
| radius_m | ✅ | m (dialog: km) | display size (scaled) |
| axial_tilt_deg, rotation_period_h | ✅ | deg, h | spin animation |
| has_ring | ✅ | bool | |
| parent | ✅ | body name / null | which `GM` to use |
| orbit.semi_major_axis_m | ✅ | m (dialog: AU) | |
| orbit.eccentricity, inclination_deg, raan_deg, arg_periapsis_deg, mean_anomaly_epoch_deg | ✅ | - / deg | |
| **position over time** | | | ✅ Kepler propagation |

The Sun has `parent: null` and `orbit: null` (it sits at the origin).

---

## B. Add a satellite (the thing you simulate)

**File:** `data/satellites.json` · **GUI:** Objects tab → right-click
*Satellites* → *Add Satellite…*

```json
{
    "name": "MySat",
    "color": "#f2f2f2",
    "mass_kg": 500.0,
    "dimensions_m": [2.0, 1.5, 1.0],
    "parent": "Earth",
    "orbit": {
        "semi_major_axis_m": 24628137.0,
        "eccentricity": 0.7207,
        "inclination_deg": 63.4,
        "raan_deg": 0.0,
        "arg_periapsis_deg": 270.0,
        "mean_anomaly_epoch_deg": 0.0
    }
}
```

| Parameter | You provide | Units | Computed for you |
|-----------|:-----------:|-------|------------------|
| name, color | ✅ | - | |
| mass_kg | ✅ | kg | |
| dimensions_m `[L,W,H]` | ✅ | m | **inertia tensor** `box_inertia` (Eq. 16) |
| parent | ✅ | body name | parent `GM` for propagation |
| orbit (6 elements) | ✅ | m, deg | position & velocity (Eq. 5–6) |
| **inertia, position, velocity, period** | | | ✅ all computed |

**Dialog convenience:** the *Add Satellite* dialog asks for **perigee altitude
(km)** and **eccentricity** instead of the semi-major axis, and computes
`a = (R_parent + perigee_alt) / (1 − e)` for you. So for a Molniya orbit you
type perigee = 500 km, e = 0.7207, i = 63.4°, arg. periapsis = 270°.

---

## C. Add a mission (a runnable scenario)

A **mission** = a satellite + the simulation parameters to run on it. Missions
let you keep several scenarios (detumble, sun-pointing, a high-tumble case…) for
the same or different satellites.

**File:** `data/missions.json` · **GUI:** Mission tab → *Add Mission…*

```json
{
    "name": "MySat - Sun-pointing",
    "satellite": "MySat",
    "description": "PD sun-pointing with reaction wheels",
    "simulation": {
        "mode": "sun_pointing",
        "rw_max_momentum_nms": 4.0,
        "n_orbits": 3.0
    }
}
```

| Parameter | You provide | Computed / merged |
|-----------|:-----------:|-------------------|
| name, description | ✅ | |
| satellite (by name) | ✅ | its mass/inertia/orbit are pulled in |
| simulation overrides (any of the keys below) | ✅ (optional) | merged onto `simulation_defaults.json` |

Anything you **omit** in `simulation` falls back to `simulation_defaults.json`.
You only specify what differs.

### The simulation parameters (and where they come from)

| Key | Meaning | Default source |
|-----|---------|----------------|
| `mode` | `detumble` / `sun_pointing` / `full` | JSON default |
| `n_orbits`, `dt_s` | duration, time step | JSON default |
| `initial_tumble_deg_s` | starting tumble rate | JSON default |
| `magnetorquer_max_dipole_am2` | torquer authority | JSON default |
| `rw_max_momentum_nms`, `rw_max_torque_nm` | wheel limits | JSON default |
| `residual_dipole_am2`, `srp_area_m2`, `reflectance`, `drag_coeff`, `cp_offset_m` | disturbance geometry | JSON default |
| `natural_freq`, `damping`, `desat_gain`, `detumble_exit_deg_s` | control tuning | JSON default |
| `bdot_gain_fraction`, `desat_trigger_fraction`, `acquire_threshold_deg`, `drag_cutoff_altitude_m`, `pointing_initial_offset_deg`, `tumble_axis`, `pointing_initial_rate_deg_s` | algorithm constants | JSON default |

### Computed automatically when you run (never entered by hand)

- **Inertia** from mass + dimensions (Eq. 16).
- **Orbit elements / period / position / velocity** from the satellite's orbit.
- **PD gains** `K_p = Iω_n²`, `K_d = 2ζIω_n` (Eq. 36).
- **B-dot gain** auto-sized to saturate the torquers near perigee.
- **Perigee field** `B_perigee` for gain sizing.
- All time-series outputs (rates, attitude error, wheel momentum, torques…).

---

## D. Run it

- **GUI:** open the **Mission** tab, pick your mission, press **Run ADCS
  simulation ▶** (or pick it on the **ADCS Simulation** tab, tweak live, and
  **Run**). Plots appear in the right-hand panel.
- **Headless:** edit `reference_satellite` / the first mission, then
  `python -m lunalink.main_simulation` → plots in `output/`.

## E. What the simulation *requires* to run

Minimum to get a valid run:

1. A **satellite** with a non-null `orbit` and a `parent` whose `GM` is known
   (any body in `GM_BODIES`, else it falls back to `GM_EARTH`).
2. A **mission** pointing at that satellite (or just rely on the JSON defaults +
   `reference_satellite`).

Everything else has a sensible default in `simulation_defaults.json`, so the
smallest possible mission is just `{name, satellite}`.

---

See [09-verification](09-verification.md) for how each computed quantity is
checked against the framework, and [README](README.md) to jump to any chapter.
