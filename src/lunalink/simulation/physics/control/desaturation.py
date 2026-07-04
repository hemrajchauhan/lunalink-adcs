"""Reaction-wheel desaturation - magnetic cross-product law
(framework Sec. 9.3, Eq. 37).

    m = (kd / |B|^2) ((h_w - h_w_ref) x B)
    T_mtq = m x B = -kd * (h_w - h_w_ref)_perp

i.e. the torque opposes the component of the stored wheel momentum that is
perpendicular to B. (With the wheels holding attitude, h_w integrates the
external torque, so T_mtq must point *against* h_w to unload it.)

Triggered when the stored wheel momentum approaches the wheel capacity.
"""
import numpy as np


def desaturation_dipole(B_body: np.ndarray, wheel_momentum: np.ndarray,
                        gain: float, max_dipole: float,
                        wheel_ref: np.ndarray = None) -> np.ndarray:
    B2 = B_body @ B_body
    if B2 <= 0:
        return np.zeros(3)
    excess = wheel_momentum if wheel_ref is None else (wheel_momentum - wheel_ref)
    m = gain / B2 * np.cross(excess, B_body)
    return np.clip(m, -max_dipole, max_dipole)
