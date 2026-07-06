"""Eclipse test - cylindrical shadow model (framework Sec. 7.2, Eq. 26)."""
import numpy as np

from ..constants import R_EARTH_M


def is_in_eclipse(r_eci: np.ndarray, sun_hat: np.ndarray,
                  body_radius_m: float = R_EARTH_M) -> bool:
    """In shadow iff (r . s_hat < 0) and the perpendicular distance to the
    Sun line is below the body radius (framework Eq. 26)."""
    along = np.dot(r_eci, sun_hat)
    if along >= 0:
        return False                              # sunward side
    perpendicular = r_eci - along * sun_hat
    return np.linalg.norm(perpendicular) < body_radius_m
