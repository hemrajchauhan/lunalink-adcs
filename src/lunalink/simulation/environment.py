"""Space environment models (framework Sec. 7).

Sun direction, eclipse test, geomagnetic field and atmospheric density - the
inputs the disturbance torques and control laws need. All vectors are in the
Earth-Centred Inertial (ECI) frame and SI units.
"""
import numpy as np

from ..config import GM_EARTH

R_EARTH_M = 6.378e6
OBLIQUITY_RAD = np.radians(23.44)
GEOMAG_DIPOLE_TM3 = 7.94e15          # M_B, geomagnetic dipole strength (T m^3)


def sun_unit_vector(time_s: float, epoch_days_j2000: float = 0.0) -> np.ndarray:
    """Low-precision analytic Sun direction in ECI (framework Eq. 23-25)."""
    d = epoch_days_j2000 + time_s / 86400.0
    mean_lon = np.radians(280.46 + 0.9856474 * d)
    mean_anom = np.radians(357.528 + 0.9856003 * d)
    ecl_lon = mean_lon + np.radians(1.915) * np.sin(mean_anom) \
        + np.radians(0.020) * np.sin(2 * mean_anom)
    return np.array([
        np.cos(ecl_lon),
        np.cos(OBLIQUITY_RAD) * np.sin(ecl_lon),
        np.sin(OBLIQUITY_RAD) * np.sin(ecl_lon),
    ])


def is_in_eclipse(r_eci: np.ndarray, sun_hat: np.ndarray,
                  body_radius_m: float = R_EARTH_M) -> bool:
    """Cylindrical-shadow eclipse test (framework Eq. 26)."""
    along = np.dot(r_eci, sun_hat)
    if along >= 0:
        return False                                   # sunward side
    perp = r_eci - along * sun_hat
    return np.linalg.norm(perp) < body_radius_m


def magnetic_field_eci(r_eci: np.ndarray,
                       dipole_strength_tm3: float = GEOMAG_DIPOLE_TM3) -> np.ndarray:
    """Tilted/aligned-dipole geomagnetic field in ECI (framework Eq. 27).

    Uses the aligned-dipole simplification m_hat = -z_hat (state this
    assumption in the report). Returns the field vector (T)."""
    r = np.linalg.norm(r_eci)
    if r == 0:
        return np.zeros(3)
    r_hat = r_eci / r
    m_hat = np.array([0.0, 0.0, -1.0])
    return dipole_strength_tm3 / r ** 3 * (3 * np.dot(m_hat, r_hat) * r_hat - m_hat)


def atmospheric_density(altitude_m: float, rho0: float = 1e-12,
                        h0_m: float = 500e3, scale_height_m: float = 60e3) -> float:
    """Exponential atmosphere (framework Eq. 28); negligible above ~600 km."""
    return rho0 * np.exp(-(altitude_m - h0_m) / scale_height_m)
