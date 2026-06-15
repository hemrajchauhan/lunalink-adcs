# =============================================================================
#  LunaLink ADCS Simulator - Configuration (GUI / visualization only)
# =============================================================================
#  Mission, orbit, spacecraft and simulation PARAMETERS are NOT here - they live
#  in the JSON data files (bodies.json, satellites.json, missions.json,
#  simulation_defaults.json, mission_profile.json). This module only holds GUI
#  window sizes and display-scaling constants.
# =============================================================================

# Physical constants are re-exported from the single source of truth so legacy
# imports (e.g. ``from ..config import GM_EARTH``) keep working.
from .simulation.physics.constants import GM_SUN, GM_EARTH, AU_M  # noqa: F401

# -----------------------------------------------------------------------------
#  GUI window parameters
# -----------------------------------------------------------------------------
MAIN_WINDOW_WIDTH = 2_000
MAIN_WINDOW_HEIGHT = 1_200
LEFT_WINDOW_WIDTH = 1_400
RIGHT_WINDOW_WIDTH = MAIN_WINDOW_WIDTH - LEFT_WINDOW_WIDTH
CONTROL_PANEL_HEIGHT = 700
PLOT_PANEL_HEIGHT = MAIN_WINDOW_HEIGHT - CONTROL_PANEL_HEIGHT

# -----------------------------------------------------------------------------
#  VISUALIZATION scaling (display only - NOT physically to scale)
# -----------------------------------------------------------------------------
#  Real astronomical ratios cannot be shown to scale (planets would be
#  invisible dots light-years apart), so distances and body sizes use
#  independent, tunable mappings.

# Planet orbital radius (around the Sun): 1 AU -> this many scene units.
# Larger value spreads the planets out (linear, so proportions stay real).
AU_TO_UNITS = 120.0

# Body display radius = BODY_SIZE_COEFF * radius_m ** BODY_SIZE_POWER,
# then clamped. A sub-linear power keeps the Sun from swallowing the planets
# while still preserving size ordering.
BODY_SIZE_POWER = 0.40
BODY_SIZE_COEFF = 0.010
BODY_DISPLAY_RADIUS_MIN = 1.5
BODY_DISPLAY_RADIUS_MAX = 14.0

# Moons: semi-major axis is drawn at this multiple of the parent's display
# radius (small + bounded, so a moon clearly orbits its parent and never reaches
# a neighbouring planet).
MOON_SEMI_MAJOR_FACTOR = 2.5

# Satellites: perigee is drawn at this multiple of the parent's display radius
# (just clear of the surface); the eccentric orbit shape is preserved.
SATELLITE_PERIGEE_FACTOR = 1.25

# Satellites are physically metres-sized next to a planet; draw them as a small
# fixed-size marker so they remain visible.
SATELLITE_DISPLAY_SIZE = 0.6

# Time: how many simulated seconds pass per real animation second, and the
# animation refresh rate. Default is gentle (1 sim-hour per real second) so
# rotations are visible; the Visualization tab slider goes much faster for
# watching orbital motion.
TIME_ACCELERATION = 3_600.0          # 1 sim-hour per real second
ANIMATION_FPS = 30
TIME_ACCEL_MIN = 1.0                 # real-time
TIME_ACCEL_MAX = 5_184_000.0         # 60 days per real second

# Starfield
STAR_COUNT = 450
STAR_FIELD_RADIUS = 6_000.0
