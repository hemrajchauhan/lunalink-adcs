"""Attitude control laws (framework Sec. 9)."""
from .detumble import bdot_dipole, magnetorquer_torque, auto_gain
from .pointing import pd_gains, pd_torque
from .desaturation import desaturation_dipole

__all__ = [
    "bdot_dipole", "magnetorquer_torque", "auto_gain",
    "pd_gains", "pd_torque", "desaturation_dipole",
]
