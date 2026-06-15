"""Kepler's equation and orbit timing (framework Sec. 3.1-3.2, Eq. 2-3).

    M = E - e sin E              (Kepler's equation)
    n = sqrt(mu / a^3)           (mean motion, Eq. 2)
    P = 2 pi sqrt(a^3 / mu)      (period, Eq. 2)
"""
import numpy as np


def solve_kepler(mean_anomaly_rad: float, eccentricity: float,
                 tolerance: float = 1e-10, max_iterations: int = 50) -> float:
    """Solve M = E - e sin E for the eccentric anomaly E by Newton iteration
    (framework Eq. 3)."""
    M = (mean_anomaly_rad + np.pi) % (2 * np.pi) - np.pi   # wrap to [-pi, pi]
    E = M if eccentricity < 0.8 else np.pi                 # good first guess
    for _ in range(max_iterations):
        delta = (E - eccentricity * np.sin(E) - M) / (1 - eccentricity * np.cos(E))
        E -= delta
        if abs(delta) < tolerance:
            break
    return E


def mean_motion(semi_major_axis_m: float, mu: float) -> float:
    """Mean motion n = sqrt(mu / a^3)  (rad/s)."""
    return np.sqrt(mu / semi_major_axis_m ** 3)


def orbital_period_s(semi_major_axis_m: float, mu: float) -> float:
    """Orbital period P = 2 pi / n  (s)."""
    return 2 * np.pi / mean_motion(semi_major_axis_m, mu)
