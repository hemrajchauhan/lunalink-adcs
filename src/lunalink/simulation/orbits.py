"""Backward-compatibility shim.

The orbit mechanics now live in :mod:`lunalink.simulation.physics.orbit`
(split into kepler / propagation / builders). This module just re-exports them
so existing ``simulation.orbits`` imports keep working.
"""
from .physics.orbit import (  # noqa: F401
    solve_kepler, mean_motion, orbital_period_s,
    position_in_parent_frame, state_vectors_in_parent_frame, orbit_path_points,
    circular_orbit_from_altitude, orbit_from_apsides,
)
