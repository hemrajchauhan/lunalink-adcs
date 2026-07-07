"""Solar-radiation-pressure torque (framework Sec. 6.2, Eq. 20).

    F_srp = -(Phi/c) A_s (1+q) s_hat   (force on the illuminated area)
    T_srp = rho_cp x F_srp

Zero in eclipse. Roughly constant in sunlight; dominant at apogee.
"""
import numpy as np

from ..constants import SOLAR_CONST_W_M2, LIGHT_SPEED_M_S


def solar_radiation(R_bi: np.ndarray, sun_hat_eci: np.ndarray, in_eclipse: bool,
                    area_m2: float, reflectance: float,
                    cp_offset_body: np.ndarray, flux_scale: float = 1.0) -> np.ndarray:
    """``flux_scale`` scales the solar constant for the parent body's distance
    from the Sun (``(1 AU / heliocentric distance)^2``); 1.0 for an Earth orbit."""
    if in_eclipse:
        return np.zeros(3)
    sun_body = R_bi @ sun_hat_eci
    force = -(SOLAR_CONST_W_M2 * flux_scale / LIGHT_SPEED_M_S) \
        * area_m2 * (1 + reflectance) * sun_body
    return np.cross(cp_offset_body, force)
