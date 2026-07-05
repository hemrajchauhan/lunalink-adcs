# 03 - Attitude Representation & Kinematics (Framework Sec. 4)

How we describe *which way the spacecraft is pointing* and how that orientation
changes with the body rotation rate.

**Code:** `simulation/physics/attitude/` → `quaternion.py`, `pointing.py`

## 3.1 The quaternion (Eq. 12)

We use a **scalar-last unit quaternion** `q = [q1, q2, q3, q4]` (`q4` is the
scalar part), with no singularities (unlike Euler angles). The **body←inertial
rotation matrix** is:

```
R(q) = (q4² − qᵥ·qᵥ) I₃ + 2 qᵥ qᵥᵀ − 2 q4 [qᵥ×]
```

where `[a×]` is the cross-product (skew) matrix.

**Code:** `quaternion.quat_to_matrix(q)` (Eq. 12), `quaternion.skew(a)`.

> **Convention note.** `matrix_to_quat()` is written to be the *exact inverse*
> of `quat_to_matrix()` (it returns the conjugate of the standard Shepperd
> result, because our `R(q)` uses the `−2q4[qᵥ×]` body←inertial convention).
> Getting this wrong made the controller point *away* from the Sun in an early
> version - it is now verified by a round-trip test.

## 3.2 Kinematic ODE (Eq. 13)

The orientation evolves from the body angular velocity `ω`:

```
q̇ = ½ Ω(ω) q
        ⎡  0   ω3  −ω2  ω1 ⎤
Ω(ω) =  ⎢ −ω3   0   ω1  ω2 ⎥
        ⎢  ω2  −ω1   0   ω3 ⎥
        ⎣ −ω1  −ω2  −ω3   0 ⎦
```

**Code:** `quaternion.quat_derivative(q, ω)` - integrated together with the
dynamics (Eq. 18) in the RK4 loop, and `q` is re-normalised every step.

## 3.3 Euler angles - for reporting only (Eq. 14)

We convert `q → (roll, pitch, yaw)` (3‑2‑1) **only for plots**, never as the
integration state (Euler angles hit gimbal lock at pitch = ±90°).

**Code:** `pointing.quat_to_euler321(q)`.

## 3.4 Pointing-error metric (Eq. 15)

A single scalar for "how far off target are we?":

```
θ_err = arccos( b̂_actual · b̂_target ),   b̂_target = R(q) · t̂_I
```

where `t̂_I` is the desired direction in the inertial frame (the Sun line for
sun-pointing). `b̂_actual` is the body axis we want on target (the +z face).

**Code:** `pointing.pointing_error_deg(q, target_inertial, body_axis=[0,0,1])`.

## 3.5 Building a command attitude

For sun-pointing we need a *commanded* quaternion that puts the body +z axis on
the Sun. `pointing.target_dcm_point_axis(sun)` builds an orthonormal
body←inertial DCM with +z along the Sun, and `matrix_to_quat()` converts it to
`q_cmd`. The control law then drives the **error quaternion**
`q_e = q_cmd⁻¹ ⊗ q` (Eq. 35) to identity.

**Code:** `pointing.quat_error(q_cmd, q)`, `quaternion.quat_multiply`,
`quaternion.quat_conjugate`.

## ✅ Cross-check vs the framework

- `quat_to_matrix` matches Eq. 12 term-for-term.
- `quat_derivative` matches the `Ω(ω)` matrix in Eq. 13 exactly.
- Round-trip `quat_to_matrix(matrix_to_quat(R)) == R` verified numerically.
- `‖q‖ = 1` is enforced each step (re-normalisation), as the framework requires.

Next: [04 - Rigid-body dynamics](04-rigid-body-dynamics.md).
