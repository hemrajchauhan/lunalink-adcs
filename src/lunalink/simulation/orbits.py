"""Keplerian orbital mechanics.

Pure, side-effect-free maths used to turn a set of classical orbital elements
into a Cartesian position in the parent body's inertial frame at a given time.
The Sun is assumed stationary (per the assignment scope), so a child's absolute
position is simply parent_position + position_in_parent_frame.
"""
import numpy as np

from .objects import OrbitElements


def solve_kepler(mean_anomaly_rad: float, eccentricity: float,
                 tolerance: float = 1e-10, max_iterations: int = 50) -> float:
    """Solve Kepler's equation ``M = E - e*sin(E)`` for eccentric anomaly E."""
    M = (mean_anomaly_rad + np.pi) % (2 * np.pi) - np.pi  # wrap to [-pi, pi]
    E = M if eccentricity < 0.8 else np.pi                # sensible first guess
    for _ in range(max_iterations):
        delta = (E - eccentricity * np.sin(E) - M) / (1 - eccentricity * np.cos(E))
        E -= delta
        if abs(delta) < tolerance:
            break
    return E


def mean_motion(semi_major_axis_m: float, mu: float) -> float:
    """Mean motion (rad/s): n = sqrt(mu / a^3)."""
    return np.sqrt(mu / semi_major_axis_m ** 3)


def orbital_period_s(semi_major_axis_m: float, mu: float) -> float:
    """Orbital period in seconds."""
    return 2 * np.pi / mean_motion(semi_major_axis_m, mu)


def _rotation_matrix(raan_rad: float, inclination_rad: float,
                     arg_periapsis_rad: float) -> np.ndarray:
    """Perifocal -> inertial rotation: Rz(RAAN) @ Rx(i) @ Rz(arg_periapsis)."""
    cos_O, sin_O = np.cos(raan_rad), np.sin(raan_rad)
    cos_i, sin_i = np.cos(inclination_rad), np.sin(inclination_rad)
    cos_w, sin_w = np.cos(arg_periapsis_rad), np.sin(arg_periapsis_rad)

    Rz_O = np.array([[cos_O, -sin_O, 0], [sin_O, cos_O, 0], [0, 0, 1]])
    Rx_i = np.array([[1, 0, 0], [0, cos_i, -sin_i], [0, sin_i, cos_i]])
    Rz_w = np.array([[cos_w, -sin_w, 0], [sin_w, cos_w, 0], [0, 0, 1]])
    return Rz_O @ Rx_i @ Rz_w


def position_in_parent_frame(elements: OrbitElements, mu: float,
                             time_s: float) -> np.ndarray:
    """Position vector (m) relative to the parent body at ``time_s``."""
    a = elements.semi_major_axis_m
    e = elements.eccentricity

    M0 = np.radians(elements.mean_anomaly_epoch_deg)
    M = M0 + mean_motion(a, mu) * time_s
    E = solve_kepler(M, e)

    # Position in the perifocal (orbital) plane.
    x_peri = a * (np.cos(E) - e)
    y_peri = a * np.sqrt(1 - e ** 2) * np.sin(E)
    r_peri = np.array([x_peri, y_peri, 0.0])

    R = _rotation_matrix(
        np.radians(elements.raan_deg),
        np.radians(elements.inclination_deg),
        np.radians(elements.arg_periapsis_deg),
    )
    return R @ r_peri


def orbit_path_points(elements: OrbitElements, samples: int = 200) -> np.ndarray:
    """Return ``samples`` points (m, parent frame) tracing the full orbit.

    Uses true anomaly sampling so the ellipse is drawn evenly regardless of
    eccentricity. Independent of time / mu - purely geometric.
    """
    a = elements.semi_major_axis_m
    e = elements.eccentricity

    nu = np.linspace(0, 2 * np.pi, samples)
    r = a * (1 - e ** 2) / (1 + e * np.cos(nu))
    x_peri = r * np.cos(nu)
    y_peri = r * np.sin(nu)
    points_peri = np.column_stack([x_peri, y_peri, np.zeros_like(nu)])

    R = _rotation_matrix(
        np.radians(elements.raan_deg),
        np.radians(elements.inclination_deg),
        np.radians(elements.arg_periapsis_deg),
    )
    return points_peri @ R.T


def circular_orbit_from_altitude(parent_radius_m: float, altitude_m: float,
                                 inclination_deg: float = 0.0,
                                 raan_deg: float = 0.0,
                                 mean_anomaly_epoch_deg: float = 0.0) -> OrbitElements:
    """Convenience builder: a circular orbit at a given altitude above a body."""
    return OrbitElements(
        semi_major_axis_m=parent_radius_m + altitude_m,
        eccentricity=0.0,
        inclination_deg=inclination_deg,
        raan_deg=raan_deg,
        mean_anomaly_epoch_deg=mean_anomaly_epoch_deg,
    )


def orbit_from_apsides(parent_radius_m: float, perigee_altitude_m: float,
                       apogee_altitude_m: float, inclination_deg: float = 0.0,
                       raan_deg: float = 0.0, arg_periapsis_deg: float = 0.0,
                       mean_anomaly_epoch_deg: float = 0.0) -> OrbitElements:
    """Build elements from perigee/apogee altitudes (e.g. a Molniya orbit)."""
    r_p = parent_radius_m + perigee_altitude_m
    r_a = parent_radius_m + apogee_altitude_m
    a = 0.5 * (r_p + r_a)
    e = (r_a - r_p) / (r_a + r_p)
    return OrbitElements(
        semi_major_axis_m=a,
        eccentricity=e,
        inclination_deg=inclination_deg,
        raan_deg=raan_deg,
        arg_periapsis_deg=arg_periapsis_deg,
        mean_anomaly_epoch_deg=mean_anomaly_epoch_deg,
    )
