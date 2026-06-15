# 05 — Environment Models (Framework Sec. 7)

These give the *inputs* the disturbance torques and control laws need at the
spacecraft's current position. All vectors are in the Earth-Centred Inertial
(ECI) frame, SI units.

**Code:** `simulation/physics/environment/` → `sun.py`, `eclipse.py`,
`geomagnetic.py`, `atmosphere.py`

## 5.1 Sun direction (Eq. 23–25)

Low-precision analytic ephemeris (`d` = days from J2000):

```
λ_mean = 280.46° + 0.9856474° · d
g      = 357.528° + 0.9856003° · d
λ_ecl  = λ_mean + 1.915°·sin g + 0.020°·sin 2g
ŝ_I    = [ cos λ_ecl,  cos ε · sin λ_ecl,  sin ε · sin λ_ecl ]      (ε = 23.44°)
```

**Code:** `sun.sun_unit_vector(time_s, epoch_days_j2000=0)`.
Used as the sun-pointing target and as the SRP / eclipse input.

## 5.2 Eclipse (Eq. 26)

Cylindrical-shadow test:

```
in shadow  ⇔  (r · ŝ < 0)  AND  | r − (r·ŝ) ŝ | < R_E
```

**Code:** `eclipse.is_in_eclipse(r_eci, sun_hat)`.
Gates SRP off in shadow. For a HEO, eclipses cluster near perigee and are
seasonal — some epochs see none, which is physically correct.

## 5.3 Geomagnetic field (Eq. 27)

Tilted/aligned-dipole model:

```
B(r) = (M_B / R³) [ 3 (m̂ · r̂) r̂ − m̂ ]
```

**Code:** `geomagnetic.magnetic_field_eci(r_eci)`, with `M_B = 7.94e15 T·m³`
(`constants.GEOMAG_DIPOLE_TM3`). Needed in **vector** form (not just `|B|`) for
the B-dot detumbler and the magnetic desaturation law.

## 5.4 Atmospheric density (Eq. 28)

Exponential model, only relevant near the 500 km perigee:

```
ρ(h) = ρ₀ · exp( −(h − h₀) / H_s )
```

**Code:** `atmosphere.atmospheric_density(altitude_m, rho0=1e-12, h0=500 km,
scale_height=60 km)`. The simulator only calls it below
`drag_cutoff_altitude_m` (600 km, from JSON); above that, drag is set to zero.

## ✅ Cross-check vs the framework

- Sun ephemeris matches Eq. 23–25 coefficient-for-coefficient.
- Eclipse test matches Eq. 26.
- `B` matches Eq. 27; `|B|` at perigee ≈ `M_B/R³` ≈ 2.4×10⁻⁵ T (used to verify
  the magnetic torque magnitude in [06](06-disturbance-torques.md)).

## ⚠️ Assumptions to state in a report

- **Aligned dipole** `m̂ = −ẑ_E` (the framework also allows tilted dipole or
  IGRF — we use the simplest, and say so).
- Density `ρ₀ ~ 10⁻¹²` kg/m³ at 500 km — solar-activity dependent (varies ~10×);
  pick and state your case.

Next: [06 — Disturbance torques](06-disturbance-torques.md).
