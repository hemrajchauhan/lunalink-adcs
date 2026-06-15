"""B-dot detumbling controller (framework Sec. 9.1, Eq. 33-34).

    m = k (omega x B)      (B-dot approximation of m = -k B_dot)
    T_c = m x B

Drives the body rate to zero using only the magnetometer rate and magnetorquers.
The commanded dipole is clipped to the magnetorquer limit.
"""
import numpy as np


def bdot_dipole(omega_body: np.ndarray, B_body: np.ndarray, gain: float,
                max_dipole: float) -> np.ndarray:
    m = gain * np.cross(omega_body, B_body)
    return np.clip(m, -max_dipole, max_dipole)


def magnetorquer_torque(dipole_body: np.ndarray, B_body: np.ndarray) -> np.ndarray:
    return np.cross(dipole_body, B_body)


def auto_gain(max_dipole: float, tumble_rate_rad_s: float, field_perigee_t: float,
              fraction: float = 0.5) -> float:
    """Pick a gain so the commanded dipole roughly saturates the magnetorquers
    near perigee (strongest field)."""
    return fraction * max_dipole / (max(tumble_rate_rad_s, 1e-6) * field_perigee_t)
