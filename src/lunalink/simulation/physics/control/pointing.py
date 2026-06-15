"""Quaternion-PD pointing controller with reaction wheels
(framework Sec. 9.2, Eq. 35-36).

    T_c = -Kp q_e,v - Kd omega_e
    Kp = I omega_n^2,   Kd = 2 zeta I omega_n
"""
import numpy as np


def pd_gains(inertia: np.ndarray, natural_freq: float, damping: float):
    """Per-axis PD gains from natural frequency and damping (Eq. 36)."""
    Kp = inertia * natural_freq ** 2
    Kd = 2 * damping * inertia * natural_freq
    return Kp, Kd


def pd_torque(q_error_vec: np.ndarray, omega_error: np.ndarray,
              Kp: np.ndarray, Kd: np.ndarray) -> np.ndarray:
    """Commanded control torque (Eq. 35). Wheels realise it via h_w_dot = -T_c."""
    return -Kp * q_error_vec - Kd * omega_error
