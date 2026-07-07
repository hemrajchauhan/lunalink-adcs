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
# Two columns: 3D scene | controls + plots (mission details live inside the
# Mission tab).
SCENE_WIDTH = 1_500
CENTER_WIDTH = MAIN_WINDOW_WIDTH - SCENE_WIDTH
# In the centre column the controls stay compact so the plots get the room.
CONTROL_PANEL_HEIGHT = 730
PLOT_PANEL_HEIGHT = MAIN_WINDOW_HEIGHT - CONTROL_PANEL_HEIGHT

# -----------------------------------------------------------------------------
#  VISUALIZATION scaling (display only - NOT physically to scale)
# -----------------------------------------------------------------------------
#  Real astronomical ratios cannot be shown to scale (planets would be
#  invisible dots light-years apart), so distances and body sizes use
#  independent, tunable mappings.

# Planet orbital radius (around the Sun): 1 AU -> this many scene units.
# Larger value spreads the planets out (linear, so proportions stay real).
# Spread wide enough that Earth's satellite + Moon subsystem fits comfortably
# between Venus and Mars without any orbit lines crossing.
AU_TO_UNITS = 240.0

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
SATELLITE_PERIGEE_FACTOR = 1.1

# When a moon and a satellite share a parent, keep the moon's closest approach
# at least this multiple of the satellite's farthest point, so a moon never
# crosses a satellite's (possibly very eccentric) orbit in the display.
MOON_SATELLITE_CLEARANCE = 1.2

# Satellites are physically metres-sized next to a planet; draw them as a small
# fixed-size marker so they remain visible.
SATELLITE_DISPLAY_SIZE = 0.6

# Body-axes triad drawn on a satellite during an attitude playback: length as a
# multiple of the satellite marker size (long enough to read the orientation).
SATELLITE_AXES_LENGTH_FACTOR = 4.5

# Attitude playback: after a simulation, the satellite's orientation history is
# replayed over this many real seconds (regardless of the orbit-view speed
# slider) so the whole detumble / pointing sequence is watchable rather than
# flashing by. When it finishes, the satellite reverts to a plain box.
ATTITUDE_PLAYBACK_SECONDS = 18.0

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
STAR_FIELD_RADIUS = 16_000.0
STAR_COLOR = "white"
STAR_POINT_SIZE = 1.5

# -----------------------------------------------------------------------------
#  Scene appearance (colours / sizes for the 3D view)
# -----------------------------------------------------------------------------
SCENE_BACKGROUND = "#0a0e1a"
SUN_LIGHT_INTENSITY = 1.4
FILL_LIGHT_INTENSITY = 0.18
AXIS_COLORS = ("#ff6b6b", "#5cd65c", "#5b9bff")   # X, Y, Z
SPHERE_RESOLUTION = 48
BODY_FALLBACK_COLOR = "#999999"
SUN_GLOW_COLOR = "#ffe08a"
SATURN_RING_COLOR = "#cbb98f"
ORBIT_COLOR_BODY = "#6688aa"
ORBIT_COLOR_SATELLITE = "#46e0a0"
SATELLITE_EDGE_COLOR = "#333333"
LABEL_COLOR = "white"
LABEL_FONT_SIZE = 11
INSPECT_TEXT_COLOR = "white"
INSPECT_FONT_SIZE = 10
