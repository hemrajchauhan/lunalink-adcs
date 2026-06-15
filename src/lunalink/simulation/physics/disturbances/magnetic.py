"""Residual-dipole magnetic torque (framework Sec. 6.3, Eq. 21).

    T_mag = D_res x B

D_res is the spacecraft's residual magnetic dipole (body frame, A m^2),
B is the geomagnetic field in body axes (T). Cyclic; matters near perigee.
"""
import numpy as np


def magnetic(residual_dipole_body: np.ndarray, B_body: np.ndarray) -> np.ndarray:
    return np.cross(residual_dipole_body, B_body)
