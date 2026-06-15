"""Space environment models (framework Sec. 7)."""
from ..constants import GEOMAG_DIPOLE_TM3, R_EARTH_M
from .sun import sun_unit_vector
from .eclipse import is_in_eclipse
from .geomagnetic import magnetic_field_eci
from .atmosphere import atmospheric_density

__all__ = [
    "sun_unit_vector", "is_in_eclipse", "magnetic_field_eci",
    "atmospheric_density", "GEOMAG_DIPOLE_TM3", "R_EARTH_M",
]
