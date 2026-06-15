"""Geomagnetic field - tilted/aligned dipole (framework Sec. 7.3, Eq. 27).

    B(r) = (M_B / R^3) [ 3 (m_hat . r_hat) r_hat - m_hat ]

Uses the aligned-dipole simplification m_hat = -z_hat (state this assumption in
the report). Returns the field vector (T) in ECI.
"""
import numpy as np

from ..constants import GEOMAG_DIPOLE_TM3


def magnetic_field_eci(r_eci: np.ndarray,
                       dipole_strength_tm3: float = GEOMAG_DIPOLE_TM3) -> np.ndarray:
    r = np.linalg.norm(r_eci)
    if r == 0:
        return np.zeros(3)
    r_hat = r_eci / r
    m_hat = np.array([0.0, 0.0, -1.0])
    return dipole_strength_tm3 / r ** 3 * (3 * np.dot(m_hat, r_hat) * r_hat - m_hat)
