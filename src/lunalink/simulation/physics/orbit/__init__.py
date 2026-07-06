"""Orbit mechanics (framework Sec. 3)."""
from .kepler import solve_kepler, mean_motion, orbital_period_s
from .propagation import (
    position_in_parent_frame, state_vectors_in_parent_frame, orbit_path_points,
)
from .builders import circular_orbit_from_altitude, orbit_from_apsides
from .j2 import (
    j2_secular_rates, drift_over_window, CRITICAL_INCLINATION_DEG,
)

__all__ = [
    "solve_kepler", "mean_motion", "orbital_period_s",
    "position_in_parent_frame", "state_vectors_in_parent_frame",
    "orbit_path_points", "circular_orbit_from_altitude", "orbit_from_apsides",
    "j2_secular_rates", "drift_over_window", "CRITICAL_INCLINATION_DEG",
]
