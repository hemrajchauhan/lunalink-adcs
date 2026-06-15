"""Rigid-body dynamics and mass properties (framework Sec. 5)."""
from .mass_properties import box_inertia
from .rigid_body import state_derivative

__all__ = ["box_inertia", "state_derivative"]
