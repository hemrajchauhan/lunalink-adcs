"""Actuator models and sizing (framework Sec. 8)."""
from .sizing import (
    slew_sizing, cyclic_storage, magnetorquer_dipole, sizing_summary,
)

__all__ = ["slew_sizing", "cyclic_storage", "magnetorquer_dipole", "sizing_summary"]
