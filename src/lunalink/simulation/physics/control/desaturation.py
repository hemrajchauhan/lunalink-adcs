"""Reaction-wheel desaturation - magnetic cross-product law
(framework Sec. 9.3, Eq. 37).

    m = (kd / |B|^2) (B x (h_w - h_w_ref))
    T_mtq = m x B   (opposes the stored wheel momentum, component perpendicular to B)

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
    m = gain / B2 * np.cross(B_body, excess)
    return np.clip(m, -max_dipole, max_dipole)
