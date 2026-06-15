"""Disturbance torques (framework Sec. 6)."""
from .gravity_gradient import gravity_gradient
from .solar_radiation import solar_radiation
from .magnetic import magnetic
from .aerodynamic import aerodynamic

__all__ = ["gravity_gradient", "solar_radiation", "magnetic", "aerodynamic"]
