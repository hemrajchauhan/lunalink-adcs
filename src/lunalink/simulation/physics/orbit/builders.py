"""Convenience builders for orbital elements from intuitive inputs
(altitude, or perigee/apogee), used when adding satellites/missions.
"""
from ...objects import OrbitElements


def circular_orbit_from_altitude(parent_radius_m: float, altitude_m: float,
                                 inclination_deg: float = 0.0, raan_deg: float = 0.0,
                                 mean_anomaly_epoch_deg: float = 0.0) -> OrbitElements:
    """Circular orbit at a given altitude above the parent surface."""
    return OrbitElements(
        semi_major_axis_m=parent_radius_m + altitude_m,
        eccentricity=0.0, inclination_deg=inclination_deg,
        raan_deg=raan_deg, mean_anomaly_epoch_deg=mean_anomaly_epoch_deg)


def orbit_from_apsides(parent_radius_m: float, perigee_altitude_m: float,
                       apogee_altitude_m: float, inclination_deg: float = 0.0,
                       raan_deg: float = 0.0, arg_periapsis_deg: float = 0.0,
                       mean_anomaly_epoch_deg: float = 0.0) -> OrbitElements:
    """Elements from perigee/apogee altitudes (e.g. a Molniya orbit,
    framework Sec. 1 derived orbit)."""
    r_p = parent_radius_m + perigee_altitude_m
    r_a = parent_radius_m + apogee_altitude_m
    a = 0.5 * (r_p + r_a)
    e = (r_a - r_p) / (r_a + r_p)
    return OrbitElements(
        semi_major_axis_m=a, eccentricity=e, inclination_deg=inclination_deg,
        raan_deg=raan_deg, arg_periapsis_deg=arg_periapsis_deg,
        mean_anomaly_epoch_deg=mean_anomaly_epoch_deg)
