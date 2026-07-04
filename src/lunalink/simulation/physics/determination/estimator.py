"""Multiplicative complementary filter for attitude + gyro-bias estimation.

This is the tractable alternative to a full multiplicative EKF: it gives the
same two outputs the lecture's pointing budget needs - a high-rate attitude
estimate and an online gyro-bias estimate - with two scalar gains instead of a
covariance matrix.

State:  q_hat (estimated attitude), b_hat (estimated gyro bias).

Propagate (every step, with the gyro):
    q_hat <- integrate(q_hat, w_meas - b_hat, dt)        # RK4, drifts with bias error

Correct (only when a star fix arrives, ``T`` seconds after the previous one):
    a      = 2 * vec(q_hat^{-1} (x) q_meas)               # small-angle error, body frame
    q_hat <- q_hat (x) dq(kp * a)                         # rotate estimate toward the fix
    b_hat <- b_hat - ki * a / T                           # learn the bias from the residual

Between fixes the only thing that rotates the estimate away from the truth is
the *bias error* ``(b_true - b_hat)``, so the residual is ``a ~= -(b_true-b_hat)*T``.
Dividing the bias update by the fix interval ``T`` therefore makes it a direct,
stable estimate of that bias error (gain ``ki`` in (0, 1)), and the between-fix
drift shrinks to the star-tracker noise floor as ``b_hat -> b_true``.
"""
import numpy as np

from ..attitude import (
    quat_derivative, quat_multiply, quat_conjugate, normalize,
)


def propagate_estimate(q_hat: np.ndarray, omega: np.ndarray, dt: float) -> np.ndarray:
    """RK4-propagate the estimated quaternion under a constant body rate."""
    k1 = quat_derivative(q_hat, omega)
    k2 = quat_derivative(normalize(q_hat + 0.5 * dt * k1), omega)
    k3 = quat_derivative(normalize(q_hat + 0.5 * dt * k2), omega)
    k4 = quat_derivative(normalize(q_hat + dt * k3), omega)
    return normalize(q_hat + dt / 6.0 * (k1 + 2 * k2 + 2 * k3 + k4))


def star_update(q_hat: np.ndarray, b_hat: np.ndarray, q_meas: np.ndarray,
                kp: float, ki: float, interval_s: float):
    """Apply one star-tracker correction to ``(q_hat, b_hat)``.

    ``kp`` is the fraction of the measured attitude error fed back into the
    estimate; ``ki`` is the (dimensionless) bias-learning gain and ``interval_s``
    is the time since the previous fix, used to convert the accumulated error
    into a bias-rate estimate. Returns ``(q_hat, b_hat, a)`` where ``a`` is the
    measured small-angle error (rad, body frame).
    """
    q_err = quat_multiply(quat_conjugate(q_hat), q_meas)
    if q_err[3] < 0.0:                         # shortest rotation (q and -q equal)
        q_err = -q_err
    a = 2.0 * q_err[:3]                         # rotation vector estimate -> fix
    dq = normalize(np.array([*(0.5 * kp * a), 1.0]))
    q_hat = normalize(quat_multiply(q_hat, dq))
    b_hat = b_hat - ki * a / max(interval_s, 1e-9)
    return q_hat, b_hat, a


def knowledge_error_deg(q_hat: np.ndarray, q_true: np.ndarray) -> float:
    """Total rotation angle (deg) between the estimate and the truth."""
    q_err = quat_multiply(quat_conjugate(q_hat), q_true)
    return float(np.degrees(2.0 * np.arccos(np.clip(abs(q_err[3]), -1.0, 1.0))))
