"""Mass properties (framework Sec. 5.1, Eq. 16).

Principal inertia of a uniform solid box with sides (ax, ay, az):
    Ix = m/12 (ay^2 + az^2),  Iy = m/12 (ax^2 + az^2),  Iz = m/12 (ax^2 + ay^2)
"""
import numpy as np


def box_inertia(mass_kg: float, dims_m) -> np.ndarray:
    ax, ay, az = dims_m
    return mass_kg / 12.0 * np.array([ay ** 2 + az ** 2,
                                      ax ** 2 + az ** 2,
                                      ax ** 2 + ay ** 2])
