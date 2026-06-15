"""Maps physical quantities (metres) to scene units for display.

The mapping is deliberately NOT to scale - real astronomical ratios cannot be
visualised - so distances and body sizes use independent, tunable rules defined
in ``config``. Distances around the Sun are linear in AU; body radii use a
sub-linear power law; moons/satellites are placed relative to their parent.
"""
import numpy as np

from ...config import (
    AU_M, AU_TO_UNITS, BODY_SIZE_POWER, BODY_SIZE_COEFF,
    BODY_DISPLAY_RADIUS_MIN, BODY_DISPLAY_RADIUS_MAX,
    CHILD_ORBIT_COMPRESSION, SATELLITE_ORBIT_FACTOR,
)

# metres -> scene units for heliocentric distances
PLANET_DISTANCE_SCALE = AU_TO_UNITS / AU_M


class VisualizationTransform:

    @staticmethod
    def heliocentric_offset(offset_m: np.ndarray) -> np.ndarray:
        """Scale a Sun-relative offset (m) to scene units."""
        return np.asarray(offset_m, dtype=float) * PLANET_DISTANCE_SCALE

    @staticmethod
    def body_display_radius(radius_m: float) -> float:
        """Sub-linear, clamped mapping so the Sun does not dwarf the planets."""
        r = BODY_SIZE_COEFF * float(radius_m) ** BODY_SIZE_POWER
        return float(np.clip(r, BODY_DISPLAY_RADIUS_MIN, BODY_DISPLAY_RADIUS_MAX))

    @staticmethod
    def child_offset(offset_m: np.ndarray, parent_radius_m: float,
                     parent_display_radius: float, compression: float) -> np.ndarray:
        """Scale a parent-relative offset (m) to scene units, expressed as a
        multiple of the parent's *display* radius."""
        offset_m = np.asarray(offset_m, dtype=float)
        if parent_radius_m <= 0:
            return offset_m * 0.0
        return offset_m / parent_radius_m * parent_display_radius * compression

    @staticmethod
    def moon_offset(offset_m, parent_radius_m, parent_display_radius):
        return VisualizationTransform.child_offset(
            offset_m, parent_radius_m, parent_display_radius, CHILD_ORBIT_COMPRESSION)

    @staticmethod
    def satellite_offset(offset_m, parent_radius_m, parent_display_radius):
        return VisualizationTransform.child_offset(
            offset_m, parent_radius_m, parent_display_radius, SATELLITE_ORBIT_FACTOR)
