"""Gravity-gradient torque (framework Sec. 6.1, Eq. 19).

    T_gg = (3 mu / R^3) * (r_hat_B x I r_hat_B)

where r_hat_B = R(q) r_hat_I is nadir in body axes. Dominant near perigee.
"""
import numpy as np

from ..constants import GM_EARTH


def gravity_gradient(R_bi: np.ndarray, r_eci: np.ndarray,
                     inertia: np.ndarray, mu: float = GM_EARTH) -> np.ndarray:
    R = np.linalg.norm(r_eci)
    if R == 0:
        return np.zeros(3)
    n_body = R_bi @ (r_eci / R)            # nadir direction in body axes
    return 3.0 * mu / R ** 3 * np.cross(n_body, inertia * n_body)
