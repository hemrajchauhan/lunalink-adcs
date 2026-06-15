"""Sun direction - low-precision analytic ephemeris (framework Sec. 7.1,
Eq. 23-25). Returns the Sun unit vector in ECI.
"""
import numpy as np

from ..constants import OBLIQUITY_DEG

_OBLIQUITY = np.radians(OBLIQUITY_DEG)


def sun_unit_vector(time_s: float, epoch_days_j2000: float = 0.0) -> np.ndarray:
    d = epoch_days_j2000 + time_s / 86400.0
    mean_lon = np.radians(280.46 + 0.9856474 * d)          # Eq. 23
    mean_anom = np.radians(357.528 + 0.9856003 * d)
    ecl_lon = mean_lon + np.radians(1.915) * np.sin(mean_anom) \
        + np.radians(0.020) * np.sin(2 * mean_anom)        # Eq. 24
    return np.array([                                      # Eq. 25
        np.cos(ecl_lon),
        np.cos(_OBLIQUITY) * np.sin(ecl_lon),
        np.sin(_OBLIQUITY) * np.sin(ecl_lon),
    ])
