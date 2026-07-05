# 04 - Rigid-Body Dynamics (Framework Sec. 5)

How torques change the spacecraft's rotation rate.

**Code:** `simulation/physics/dynamics/` → `mass_properties.py`, `rigid_body.py`

## 4.1 Inertia of the box (Eq. 16)

The single most important assumption set. For a uniform solid box with side
lengths `(a_x, a_y, a_z)` and mass `m`:

```
Ix = m/12 (a_y² + a_z²)
Iy = m/12 (a_x² + a_z²)
Iz = m/12 (a_x² + a_y²)
```

**Code:** `mass_properties.box_inertia(mass_kg, dims_m)`.

This is **computed**, not entered by the user: the user supplies `mass_kg` and
`dimensions_m` (in `satellites.json`), and the inertia tensor falls out. Real
arrays/tanks would shift these - a ±20 % sensitivity sweep is a good exercise.

## 4.2 Euler's equation with reaction wheels (Eq. 17–18)

Total angular momentum is the body part plus the stored wheel momentum:

```
H = I ω + h_w
```

Conservation `Ḣ = T − ω × H`, expanded and solved for the body angular
acceleration, gives the equation we integrate:

```
I ω̇ = − ω × (I ω + h_w) − ḣ_w + T_dist
```

- `ḣ_w` is the wheel (motor) torque; the body feels the reaction `−ḣ_w`.
- `T_dist = T_gg + T_srp + T_mag + T_aero` (see [06](06-disturbance-torques.md)).
- A magnetorquer torque `T_mtq = m × B` adds into the body torque when used.

**Code:** `rigid_body.state_derivative(q, ω, I, h_w, ḣ_w, T_body)` returns
`(q̇, ω̇)` for the RK4 integrator. `T_body` already includes disturbances +
magnetorquer torque; the wheel reaction `−ḣ_w` is applied inside the function.

## 4.3 The state vector

```
x = [ q (4), ω (3), h_w (3) ]
```

`q, ω` are advanced with RK4; `h_w` is integrated with the commanded wheel
torque and clipped to the wheel capacity (saturation), with magnetic
desaturation bleeding the excess (see [07](07-actuators-and-control.md)).

## 4.4 Conserved-quantity sanity check (Eq. 5.3)

With zero external torque, `‖H‖` must be constant and rotational kinetic energy
`T_rot = ½ ωᵀ I ω` can only decrease under damping. We plot `‖H‖` (the
"Angular Momentum" tab) as an **integrator health check**.

## ✅ Cross-check vs the framework

| Quantity | Framework anchor | Code result | Match |
|----------|------------------|-------------|-------|
| Ix, Iy, Iz (box) | 135, 208, 260 kg·m² | 135.4, 208.3, 260.4 | ✅ |
| `‖H‖` drift over 1 orbit, no torque | ~0 (must be flat) | 0.03 % | ✅ |

The minimum-inertia axis is `x` (Ix smallest) - the axis gravity-gradient tries
to align with local vertical, consistent with the framework note.

Next: [05 - Environment models](05-environment-models.md).
