"""Backward-compatibility shim - see :mod:`lunalink.simulation.physics.disturbances`."""
from .physics.disturbances import (  # noqa: F401
    gravity_gradient, solar_radiation, magnetic, aerodynamic,
)
