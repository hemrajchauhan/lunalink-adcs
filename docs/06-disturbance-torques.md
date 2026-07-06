# 06 - Disturbance Torques (Framework Sec. 6)

The four environmental torques acting on the spacecraft. Each returns a torque
**vector in body axes** (N·m). `R_bi = R(q)` is the body←inertial matrix.

**Code:** `simulation/physics/disturbances/` → `gravity_gradient.py`,
`solar_radiation.py`, `magnetic.py`, `aerodynamic.py`

## 6.1 Gravity gradient (Eq. 19)

```
T_gg = (3μ / R³) · ( r̂_B × I r̂_B )
```

where `r̂_B = R(q) r̂_I` is the nadir direction in body axes and `R = |r|`.
**Dominant near perigee** (low `R`). **Code:** `gravity_gradient(R_bi, r_eci, I)`.

## 6.2 Solar radiation pressure (Eq. 20)

```
F_srp = − (Φ/c) · A_s · (1 + q_refl) · ŝ          (force on the lit area)
T_srp = ρ_cp × F_srp                               (ρ_cp = cp→cm offset)
```

Zero in eclipse. Roughly **constant in sunlight**; dominant at apogee where the
gravity-gradient and magnetic torques fade. **Code:**
`solar_radiation(R_bi, sun_hat, in_eclipse, area, reflectance, cp_offset)`.

## 6.3 Residual magnetic dipole (Eq. 21)

```
T_mag = D_res × B
```

`D_res` is the spacecraft's residual dipole (body frame, A·m²), `B` is the field
in body axes. Cyclic; matters near perigee. **Code:** `magnetic(D_res, B_body)`.

## 6.4 Aerodynamic drag (Eq. 22)

```
F_aero = − ½ ρ C_d A_r v² v̂
T_aero = ρ_cp × F_aero
```

Negligible except in the brief window around the 500 km perigee. **Code:**
`aerodynamic(R_bi, v_eci, density, Cd, area, cp_offset)`.

## The physical story (and the required plot)

`T_dist = T_gg + T_srp + T_mag + T_aero`. The "Disturbance Torque" plot shows
all four vs time:

- **Gravity gradient rules at perigee** (sharp spikes each pass, ~1/R³).
- **SRP rules at apogee** (flat, ~constant in sunlight).
- **Magnetic** is cyclic (~1/R³, peaks at perigee).
- **Aero** spikes only in the thin perigee window.

This is precisely the "torque vs orbit position" behaviour the framework
hierarchy table predicts.

## ✅ Cross-check vs the framework (LunaLink hand-calc anchors)

| Source | Framework (perigee) | Framework (apogee) | Code (peak) | Match |
|--------|--------------------:|-------------------:|------------:|:-----:|
| Gravity gradient | ~2.3×10⁻⁴ N·m | ~1×10⁻⁶ | 2.29×10⁻⁴ | ✅ |
| Magnetic (D=1) | ~5×10⁻⁵ | ~2×10⁻⁷ | 4.5×10⁻⁵ | ✅ |
| Solar pressure | ~3.3×10⁻⁶ | ~3.3×10⁻⁶ | ~2×10⁻⁶ (order) | ✅ |
| Aerodynamic | ~1.6×10⁻⁵ (ρ-dep.) | ≈0 | spikes at perigee | ✅ |

(GG perigee value depends on attitude; the worst-case `3μ/(2R³)|I_max−I_min|`
with `|260−135|` reproduces the framework's 2.3×10⁻⁴.)

## ⚠️ Implementation note

SRP uses an **effective sun-facing area** model (force along `−ŝ`, always lit in
sunlight) rather than summing individual box faces. This gives the right
order/torque and is simpler; a per-face model would refine `cos φ` per facet.

Next: [07 - Actuators & control](07-actuators-and-control.md).
