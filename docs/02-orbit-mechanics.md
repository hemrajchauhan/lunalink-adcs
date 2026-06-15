# 02 — Orbit Mechanics (Framework Sec. 3)

The orbit is evaluated **first** every time step, because position and velocity
drive every disturbance, the Sun/eclipse geometry and the magnetic field.

**Code:** `simulation/physics/orbit/` → `kepler.py`, `propagation.py`, `builders.py`

## 2.1 Shape and timing (Eq. 1–2)

From perigee/apogee radii `r_p, r_a`:

```
a = (r_p + r_a) / 2                 semi-major axis
e = (r_a − r_p) / (r_a + r_p)       eccentricity
n = √(μ / a³)                       mean motion        (rad/s)
P = 2π √(a³ / μ)                    orbital period     (s)
```

- `μ = GM` of the parent body (`physics/constants.py`: `GM_EARTH`, `GM_SUN`,
  `GM_BODIES`).
- `mean_motion()` and `orbital_period_s()` live in `kepler.py`.
- The `builders.py` helper `orbit_from_apsides()` turns perigee/apogee
  **altitudes** into `(a, e)` — this is what the "Add satellite" dialog uses.

## 2.2 Kepler propagation (Eq. 3–4)

To find where the spacecraft is at time `t`, march the **mean anomaly** and
solve **Kepler's equation** for the **eccentric anomaly** `E` with Newton
iteration:

```
M(t) = M₀ + n·t
M = E − e·sin E
E_{k+1} = E_k − (E_k − e·sin E_k − M) / (1 − e·cos E_k)
```

**Code:** `kepler.solve_kepler(M, e)` — wraps `M` to `[−π, π]`, uses a good
initial guess (`E = π` for high eccentricity), iterates to a 1e‑10 tolerance.
This is exactly framework Eq. 3.

## 2.3 Position & velocity in the inertial frame (Eq. 5–6)

The perifocal (orbit-plane) state, using the eccentric-anomaly form:

```
r_pf = [ a(cos E − e),  a√(1−e²) sin E,  0 ]
v_pf = (√(μa)/r) · [ −sin E,  √(1−e²) cos E,  0 ]      where r = a(1 − e·cos E)
```

then rotated into the parent's inertial frame with the **3‑1‑3 sequence**
`(Ω, i, ω)`:

```
R = Rz(Ω) · Rx(i) · Rz(ω)
r_I = R · r_pf          v_I = R · v_pf
```

**Code:**
- `propagation.position_in_parent_frame(elements, μ, t)` → `r_I`
- `propagation.state_vectors_in_parent_frame(elements, μ, t)` → `(r_I, v_I)`
- `_perifocal_to_inertial()` builds `R` (framework Eq. 6).

The velocity is consistent with **vis-viva** `v = √(μ(2/r − 1/a))`, which is how
we verify it (see [09-verification](09-verification.md)).

## 2.4 Building the whole system (`system.py`)

`SolarSystem` resolves **absolute** positions hierarchically: the Sun sits at
the origin (assumed stationary, per the brief), each planet is propagated
relative to the Sun, and the Moon / satellites are propagated relative to their
parent and added on top:

```
position(child) = position(parent) + position_in_parent_frame(child.orbit, μ_parent, t)
```

`mu_for(parent_name)` looks the parent's `GM` up in `GM_BODIES`.

## ✅ Cross-check vs the framework

| Quantity | Framework anchor | Code result | Match |
|----------|------------------|-------------|-------|
| LunaLink `a` | 24 628 km | 24 628 km | ✅ |
| LunaLink `e` | 0.721 | 0.7207 | ✅ |
| LunaLink period | ≈10.7 h | 10.68 h | ✅ |
| Perigee speed (vis-viva) | 9.99 km/s | 9.99 km/s | ✅ |
| Apogee speed | 1.62 km/s | 1.62 km/s | ✅ |
| Earth orbital period | 1.0 yr | 1.00 yr | ✅ |
| Neptune period | 164.8 yr | 164.7 yr | ✅ |
| Moon period | 27.3 d | 27.45 d | ✅ |

## ⚠️ Known assumptions / deviations

- **Period inconsistency (from the brief itself).** 500 × 36 000 km altitudes
  give `P ≈ 10.7 h`, not the stated "≈12 h". We keep the altitudes (so the
  disturbance, eclipse and link geometry use the real radius) and report
  10.7 h — exactly the "spot the inconsistency" the framework flags (Sec. 1).
- **Critical inclination.** At `i = 63.4°` the J2 drift of the argument of
  perigee is ~0 (Eq. 9), so we treat `ω` (arg. of perigee) as constant. We do
  **not** propagate J2 secular drift — a deliberate simplification.
- **Sun stationary.** Planets orbit a fixed Sun; we do not model the Sun's
  barycentric motion (negligible for this project).

Next: [03 — Attitude & kinematics](03-attitude-kinematics.md).
