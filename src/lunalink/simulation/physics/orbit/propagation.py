"""Position and velocity from orbital elements (framework Sec. 3.2, Eq. 4-6).

Perifocal state is rotated into the parent inertial frame with the 3-1-3
(Omega, i, omega) sequence. Velocity uses the eccentric-anomaly form, which
satisfies vis-viva (Eq. 2).
"""
import numpy as np

from ...objects import OrbitElements
from .kepler import solve_kepler, mean_motion


def _perifocal_to_inertial(raan_rad: float, inclination_rad: float,
                           arg_periapsis_rad: float) -> np.ndarray:
    """Rotation matrix Rz(Omega) Rx(i) Rz(omega) (framework Eq. 6)."""
    cO, sO = np.cos(raan_rad), np.sin(raan_rad)
    ci, si = np.cos(inclination_rad), np.sin(inclination_rad)
    cw, sw = np.cos(arg_periapsis_rad), np.sin(arg_periapsis_rad)
    Rz_O = np.array([[cO, -sO, 0], [sO, cO, 0], [0, 0, 1]])
    Rx_i = np.array([[1, 0, 0], [0, ci, -si], [0, si, ci]])
    Rz_w = np.array([[cw, -sw, 0], [sw, cw, 0], [0, 0, 1]])
    return Rz_O @ Rx_i @ Rz_w


def _rotation(elements: OrbitElements) -> np.ndarray:
    return _perifocal_to_inertial(np.radians(elements.raan_deg),
                                  np.radians(elements.inclination_deg),
                                  np.radians(elements.arg_periapsis_deg))


def _eccentric_anomaly(elements: OrbitElements, mu: float, time_s: float) -> float:
    M = np.radians(elements.mean_anomaly_epoch_deg) \
        + mean_motion(elements.semi_major_axis_m, mu) * time_s
    return solve_kepler(M, elements.eccentricity)


def position_in_parent_frame(elements: OrbitElements, mu: float,
                             time_s: float) -> np.ndarray:
    """Position (m) relative to the parent at ``time_s`` (Eq. 5-6)."""
    a, e = elements.semi_major_axis_m, elements.eccentricity
    E = _eccentric_anomaly(elements, mu, time_s)
    r_peri = np.array([a * (np.cos(E) - e),
                       a * np.sqrt(1 - e ** 2) * np.sin(E), 0.0])
    return _rotation(elements) @ r_peri


def state_vectors_in_parent_frame(elements: OrbitElements, mu: float,
                                  time_s: float) -> tuple[np.ndarray, np.ndarray]:
    """Position AND velocity (m, m/s) relative to the parent (Eq. 5-6)."""
    a, e = elements.semi_major_axis_m, elements.eccentricity
    E = _eccentric_anomaly(elements, mu, time_s)
    r_mag = a * (1 - e * np.cos(E))
    r_peri = np.array([a * (np.cos(E) - e),
                       a * np.sqrt(1 - e ** 2) * np.sin(E), 0.0])
    v_coeff = np.sqrt(mu * a) / r_mag
    v_peri = v_coeff * np.array([-np.sin(E), np.sqrt(1 - e ** 2) * np.cos(E), 0.0])
    R = _rotation(elements)
    return R @ r_peri, R @ v_peri


def orbit_path_points(elements: OrbitElements, samples: int = 200) -> np.ndarray:
    """``samples`` points (m, parent frame) tracing the full ellipse, sampled
    evenly in true anomaly. Purely geometric (no time/mu)."""
    a, e = elements.semi_major_axis_m, elements.eccentricity
    nu = np.linspace(0, 2 * np.pi, samples)
    r = a * (1 - e ** 2) / (1 + e * np.cos(nu))
    points_peri = np.column_stack([r * np.cos(nu), r * np.sin(nu), np.zeros_like(nu)])
    return points_peri @ _rotation(elements).T
