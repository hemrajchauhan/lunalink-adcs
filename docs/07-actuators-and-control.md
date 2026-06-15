# 07 — Actuators & Control (Framework Sec. 8–9)

How the spacecraft is sized and how it actually controls its attitude.

**Code:** `simulation/physics/actuators/sizing.py`,
`simulation/physics/control/` → `detumble.py`, `pointing.py`, `desaturation.py`

## 7.1 Actuator sizing (Sec. 8, Eq. 29–31)

Used for the read-only "actuator sizing" panel and the report.

```
Slew (rest-to-rest):   T_slew = 4 I θ / t²        h_slew = T_slew · t/2     (Eq. 29)
Cyclic storage:        h_store = T_D · P / 4 · 0.707                         (Eq. 30)
Magnetorquer dipole:   |m| = (margin) · T_C / B                              (Eq. 31)
```

**Code:** `sizing.slew_sizing`, `sizing.cyclic_storage`,
`sizing.magnetorquer_dipole`, and `sizing.sizing_summary(mass, dims, a)` which
the GUI calls. These are **computed** from the satellite + orbit — the user does
not enter inertia or recommended wheel size.

## 7.2 Detumbling — B-dot (Sec. 9.1, Eq. 33–34)

Remove the initial tumble using only the magnetometer rate and magnetorquers:

```
m   = k · (ω × B)        (B-dot variant of m = −k Ḃ),  clipped to |m| ≤ m_max
T_c = m × B
```

Energy argument (why it works): `Ṫ_rot = ωᵀ T_c ≤ 0`.

**Code:** `detumble.bdot_dipole(ω, B, gain, max_dipole)`,
`detumble.magnetorquer_torque(m, B)`. The gain is **auto-sized**
(`detumble.auto_gain`) so the commanded dipole saturates the torquers near
perigee, scaled by `bdot_gain_fraction` from JSON.

> **HEO reality (framework note).** B ∝ 1/R³, so torquers are effective only near
> perigee; from 10 °/s, full detumble can take *several orbits*. Over 3 orbits
> you see **partial** convergence — that is physically correct, not a bug.

## 7.3 Sun-pointing — quaternion PD + wheels (Sec. 9.2, Eq. 35–36)

```
T_c = −K_p q_{e,v} − K_d ω_e
K_p = I ω_n²        K_d = 2 ζ I ω_n         (ζ ≈ 0.7)
```

The reaction wheels realise it via `ḣ_w = −T_c`.

**Code:** `pointing.pd_gains(I, ω_n, ζ)`, `pointing.pd_torque(q_ev, ω_e, Kp, Kd)`.
`ω_n` (`natural_freq`) and `ζ` (`damping`) come from JSON.

## 7.4 Wheel desaturation — magnetic (Sec. 9.3, Eq. 37)

When stored wheel momentum nears capacity, bleed it magnetically:

```
m   = (k_d / |B|²) · ( B × (h_w − h_w,ref) )      clipped to m_max
T_c = m × B        (opposes the stored momentum, ⊥ B)
```

**Code:** `desaturation.desaturation_dipole(B, h_w, gain, max_dipole)`. The
simulator triggers it when `|h_w| > desat_trigger_fraction · h_max` and applies a
`momentum_dump_factor` reduction (both from JSON), producing the saw-tooth in
the "Reaction-Wheel Momentum" plot.

## Three scenarios (the `mode` parameter)

| `mode` | What runs | Demonstrates |
|--------|-----------|--------------|
| `detumble` | B-dot only, from the initial tumble | angular-velocity convergence |
| `sun_pointing` | PD + wheels from a near-pointed state | acquisition + momentum build-up + desaturation |
| `full` | detumble, then auto-switch to pointing once rates are low | end-to-end ConOps |

## ✅ Cross-check vs the framework

| Quantity | Framework | Code | Match |
|----------|-----------|------|-------|
| Recommended wheel `h_max` | 3–5 N·m·s | ~4.1 N·m·s | ✅ |
| Detumble over 3 HEO orbits | partial (several orbits needed) | 10 → ~7 °/s | ✅ (expected) |
| Sun-pointing steady error | small / converges | → 0.02° | ✅ |
| `ω_n`, `ζ` → `K_p`, `K_d` | Eq. 36 | exact | ✅ |

Next: [08 — The simulation loop](08-simulation-loop.md).
