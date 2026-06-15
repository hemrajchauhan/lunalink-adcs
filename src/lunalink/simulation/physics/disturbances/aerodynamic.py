"""Aerodynamic drag torque (framework Sec. 6.4, Eq. 22).

    F_aero = -1/2 rho Cd A_r v^2 v_hat
    T_aero = rho_cp x F_aero

Negligible except in the brief window around the ~500 km perigee.
"""
import numpy as np


def aerodynamic(R_bi: np.ndarray, v_eci: np.ndarray, density: float,
                drag_coeff: float, area_m2: float,
                cp_offset_body: np.ndarray) -> np.ndarray:
    v = np.linalg.norm(v_eci)
    if v == 0 or density <= 0:
        return np.zeros(3)
    v_body = R_bi @ (v_eci / v)
    force = -0.5 * density * drag_coeff * area_m2 * v ** 2 * v_body
    return np.cross(cp_offset_body, force)
