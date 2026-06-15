"""Maps physical quantities (metres) to scene units for display.

The mapping is deliberately NOT to scale - real astronomical ratios cannot be
visualised - so distances and body sizes use independent, tunable rules defined
in ``config``. Planet orbits are linear in AU; body radii use a sub-linear power
law; moons/satellites get a per-object scale so each orbit sits at a controlled,
bounded distance from its parent (and never reaches a neighbouring planet).
"""
import numpy as np

from ...config import (
    AU_M, AU_TO_UNITS, BODY_SIZE_POWER, BODY_SIZE_COEFF,
    BODY_DISPLAY_RADIUS_MIN, BODY_DISPLAY_RADIUS_MAX,
    MOON_SEMI_MAJOR_FACTOR, SATELLITE_PERIGEE_FACTOR,
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
    def child_orbit_scale(semi_major_axis_m: float, eccentricity: float,
                          parent_display_radius: float, is_satellite: bool) -> float:
        """metres -> scene-units scale for a moon/satellite orbit.

        Moons: the semi-major axis is placed at ``MOON_SEMI_MAJOR_FACTOR`` times
        the parent's display radius. Satellites: the *perigee* is placed just
        outside the parent (``SATELLITE_PERIGEE_FACTOR`` x display radius) so the
        body stays clear of the surface while the orbit's eccentric shape is
        preserved. Either way the child stays local to its parent.
        """
        if semi_major_axis_m <= 0:
            return 0.0
        if is_satellite:
            perigee = semi_major_axis_m * (1.0 - eccentricity)
            return parent_display_radius * SATELLITE_PERIGEE_FACTOR / max(perigee, 1.0)
        return parent_display_radius * MOON_SEMI_MAJOR_FACTOR / semi_major_axis_m
