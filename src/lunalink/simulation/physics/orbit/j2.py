"""J2 (Earth-oblateness) secular drift rates (framework Sec. 3, Eq. 9).

The ADCS simulation treats the orbit as a fixed Keplerian ellipse. That is only
defensible if the orbit plane and apsides drift negligibly over the simulation
window. The dominant perturbation is Earth's oblateness (the J2 zonal term),
which produces *secular* (steadily accumulating) rates in three elements:

    RAAN:           Omega_dot = -3/2 n J2 (Re/p)^2 cos i
    arg. perigee:   omega_dot =  3/4 n J2 (Re/p)^2 (5 cos^2 i - 1)
    mean anomaly:   M_dot     =  3/4 n J2 (Re/p)^2 (3 cos^2 i - 1) sqrt(1-e^2)

with the semi-latus rectum p = a(1 - e^2) and mean motion n = sqrt(mu/a^3).

The apsidal rate omega_dot vanishes at the **critical inclination**
i_crit = arccos(1/sqrt(5)) ~ 63.43 deg -- which is exactly why a Molniya orbit
is flown at 63.4 deg: its apogee stays frozen over the same hemisphere. Reporting
these numbers turns the "constant-orbit assumption" into a justified figure
rather than a hand-wave.
"""
import numpy as np

from .kepler import mean_motion
from ..constants import GM_EARTH, R_EARTH_M, J2

_RAD_S_TO_DEG_DAY = np.degrees(1.0) * 86400.0
CRITICAL_INCLINATION_DEG = float(np.degrees(np.arccos(1.0 / np.sqrt(5.0))))


def j2_secular_rates(semi_major_axis_m: float, eccentricity: float,
                     inclination_deg: float, mu: float = GM_EARTH,
                     r_body_m: float = R_EARTH_M, j2: float = J2) -> dict:
    """Secular RAAN / argument-of-perigee / mean-anomaly drift rates from J2.

    Returns rates in both rad/s and deg/day, the implied nodal/apsidal
    precession periods (days), and the critical-inclination context.
    """
    a = float(semi_major_axis_m)
    e = float(eccentricity)
    i = np.radians(inclination_deg)
    n = mean_motion(a, mu)
    p = a * (1.0 - e ** 2)
    factor = n * j2 * (r_body_m / p) ** 2          # common 3/2-less coefficient

    raan_dot = -1.5 * factor * np.cos(i)
    argp_dot = 0.75 * factor * (5.0 * np.cos(i) ** 2 - 1.0)
    manom_dot = 0.75 * factor * (3.0 * np.cos(i) ** 2 - 1.0) * np.sqrt(1.0 - e ** 2)

    def _period_days(rate_rad_s):
        if abs(rate_rad_s) < 1e-30:
            return float("inf")
        return abs(2.0 * np.pi / rate_rad_s) / 86400.0

    return {
        "raan_dot_rad_s": float(raan_dot),
        "argp_dot_rad_s": float(argp_dot),
        "mean_anomaly_dot_rad_s": float(manom_dot),
        "raan_dot_deg_day": float(raan_dot * _RAD_S_TO_DEG_DAY),
        "argp_dot_deg_day": float(argp_dot * _RAD_S_TO_DEG_DAY),
        "mean_anomaly_dot_deg_day": float(manom_dot * _RAD_S_TO_DEG_DAY),
        "nodal_period_days": _period_days(raan_dot),
        "apsidal_period_days": _period_days(argp_dot),
        "critical_inclination_deg": CRITICAL_INCLINATION_DEG,
        "near_critical": bool(abs(inclination_deg - CRITICAL_INCLINATION_DEG) < 1.0),
    }


def drift_over_window(rates: dict, window_s: float) -> dict:
    """Total RAAN / argp / mean-anomaly drift (deg) accumulated over ``window_s``."""
    days = window_s / 86400.0
    return {
        "window_days": float(days),
        "raan_drift_deg": rates["raan_dot_deg_day"] * days,
        "argp_drift_deg": rates["argp_dot_deg_day"] * days,
        "mean_anomaly_drift_deg": rates["mean_anomaly_dot_deg_day"] * days,
    }
