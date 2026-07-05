# 13 · Attitude determination

Everything up to here assumes the spacecraft knows its attitude *perfectly* - the
controller is handed the true quaternion. Real ADCS has two halves: **control**
(act to reduce the error) and **determination** (estimate the attitude in the
first place). This chapter adds the determination half: a sensor suite and a
filter that produce an *estimate* `q̂`, so we can separate **knowledge** error
(estimate vs truth) from **control** error (truth vs command) - exactly the
split the lecture's pointing budget is built around.

## The pointing budget

The lecture sizes pointing to a total of **0.1°**, allocated as

```
0.1° total  =  0.01° knowledge  +  0.08° control  +  0.01° margin
```

Knowledge and control are independent error sources that add up to the pointing
performance, so the simulator now reports each one against its slice of the
budget.

## The sensors (`physics/determination/sensors.py`)

* **Rate gyro** - measures body angular velocity, but with a slowly varying
  **bias** and white **noise**: `ω_meas = ω_true + bias + noise`. Integrating it
  alone *drifts* without bound, because the bias is mistaken for real rotation.
  Modelled bias: ~4 °/hr; noise ~1 µrad/s.
* **Star tracker** - measures the absolute attitude to ~10 arcsec
  (≈ 0.003°) but only every ~20 s. Modelled as truth perturbed by a small
  random rotation.

Neither sensor is good enough alone: the gyro is smooth and fast but drifts; the
star tracker is absolute but slow and noisy. They are *complementary*.

## The filter (`physics/determination/estimator.py`)

A **multiplicative complementary filter** - the tractable cousin of a
multiplicative EKF, with two scalar gains instead of a covariance matrix. It
carries an attitude estimate `q̂` and a gyro-bias estimate `b̂`:

**Propagate** every step with the de-biased gyro:

```
q̂  ←  RK4-integrate( q̂, ω_meas − b̂, dt )
```

**Correct** only when a star fix arrives, `T` seconds after the last one:

```
a   = 2 · vec( q̂⁻¹ ⊗ q_meas )      # small-angle error, body frame
q̂  ← q̂ ⊗ δq(kp · a)               # rotate estimate toward the fix
b̂  ← b̂ − ki · a / T                # learn the bias from the residual
```

The key idea is in the bias line. Between fixes the *only* thing that rotates
the estimate away from truth is the bias error `(b_true − b̂)`, so the measured
residual is `a ≈ −(b_true − b̂)·T`. Dividing by the fix interval `T` turns that
residual into a direct, **stable** estimate of the bias error: the filter
*learns* the gyro bias online and the between-fix drift collapses to the
star-tracker noise floor. Gains: `kp = 0.7`, `ki = 0.5`.

**Large-residual gating.** The bias line relies on `a` being a *small* angle.
While the spacecraft is tumbling fast (detumble mode), the rotation between
fixes is large and wraps, so the residual no longer measures the bias error at
all; feeding it in would corrupt `b̂` by orders of magnitude. The filter
therefore skips the bias update whenever `|a| > 0.35 rad` (about 20°) and
resumes learning automatically once the rates drop
(`estimator.BIAS_LEARN_MAX_ANGLE_RAD`).

## How it runs in the loop

The estimator runs **in parallel** with the truth state (it never feeds the
controller, so the verified control behaviour is unchanged). Each step the gyro
samples the true rate, `q̂` propagates, and on the star-tracker cadence a fix
resets it. We log the knowledge error `∠(q̂, q_true)` and the bias-estimate error
every step, and reduce them to a budget over the converged tail of the run.

## Results (verified)

Starting from a 3.9 °/hr gyro bias and zero knowledge of it:

| Quantity | Value | Budget |
|---|---|---|
| Gyro bias learned | 3.9 → ~0.3 °/hr | - |
| **Knowledge error** (RMS, converged) | **≈ 0.004°** | 0.01° ✓ |
| Star-tracker noise floor | 0.003° | - |
| Control error (RMS, converged) | PD pointing error | 0.08° |

The knowledge error settles to **≈ 0.004° RMS** - just above the star-tracker
noise floor and comfortably under the 0.01° knowledge budget - once the bias has
been learned. This was checked across several random seeds (RMS 0.0044 ± 0.0001°)
and under a detumble→pointing rate profile; because the gyro tracks the true rate
almost exactly at high rates, the estimate stays locked to truth through
detumble, and the residual knowledge error is set by the bias-learning loop and
the star-tracker noise, not by the body rate.

## Where it lives in the code

| Piece | Location |
|---|---|
| Gyro + star-tracker models | `simulation/physics/determination/sensors.py` |
| Complementary filter (propagate + star update) | `simulation/physics/determination/estimator.py` |
| Parameters (bias, noise, rate, gains, seed) | `data/simulation_defaults.json` |
| Loop wiring + pointing-budget summary | `simulation/simulator.py` (`result["determination"]`) |
| Headless `pointing_budget.png` + printout | `main_simulation.py` |
| GUI "Determination" plot tab | `gui/views/plot_tabs/determination_tab.py` |

## Cross-check vs the framework

| Framework concept | Our implementation |
|---|---|
| Sensor suite (gyro, star tracker) | `sensors.py` - biased/noisy gyro, noisy slow star tracker |
| Sensor fusion / estimation | Multiplicative complementary filter with online bias estimation |
| Pointing budget 0.1° = 0.01° + 0.08° + 0.01° | `result["determination"]` splits knowledge vs control vs budget |
| "Perfect knowledge" simplification (rest of sim) | Made explicit: knowledge error now quantified, not assumed zero |
