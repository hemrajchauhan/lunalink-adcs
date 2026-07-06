"""Atmospheric density - exponential model (framework Sec. 7.4, Eq. 28).

    rho(h) = rho0 exp(-(h - h0) / Hs)

Only meaningful near the ~500 km perigee; negligible above ~600 km.
"""
import numpy as np


def atmospheric_density(altitude_m: float, rho0: float = 1e-12,
                        h0_m: float = 500e3, scale_height_m: float = 60e3) -> float:
    return rho0 * np.exp(-(altitude_m - h0_m) / scale_height_m)
