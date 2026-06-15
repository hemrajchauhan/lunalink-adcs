# =============================================================================
#  LunaLink ADCS Simulator - Configuration
# =============================================================================
#  Mission parameters are FIXED by the Project X brief (TUM SS2026).
#  Everything below the "VISUALIZATION" block is display-only and may be tuned
#  live from the Visualization tab without affecting the physics.
# =============================================================================

# -----------------------------------------------------------------------------
#  Mission parameters (fixed by the brief)
# -----------------------------------------------------------------------------
ORBIT_TYPE = "HEO — Molniya-type (500 × 36,000 km)"
INCLINATION = 63.4              # degrees
ORBITAL_PERIOD = 12             # hours
POWER_BUDGET_EOL = 1.2          # kW
DESIGN_LIFETIME = 5             # years
EARTH_DOWNLINK = "X-band · ≥ 100 Mbps"
MOON_UPLINK = "UHF · 400–512 MHz"
GROUND_STATION = "Ottobrunn, Germany (48.07° N, 11.65° E)"
MIN_ELEVATION = 5               # degrees

# Molniya geometry derived from the brief (perigee/apogee altitudes)
HEO_PERIGEE_ALTITUDE_M = 500_000.0       # 500 km
HEO_APOGEE_ALTITUDE_M = 36_000_000.0     # 36 000 km

# -----------------------------------------------------------------------------
#  Physical constants (SI, used by the orbital propagator)
# -----------------------------------------------------------------------------
GM_SUN = 1.327_124_400_18e20    # m^3 / s^2
GM_EARTH = 3.986_004_418e14     # m^3 / s^2
AU_M = 1.495_978_707e11         # m (astronomical unit)

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
AU_TO_UNITS = 80.0

# Body display radius = BODY_SIZE_COEFF * radius_m ** BODY_SIZE_POWER,
# then clamped. A sub-linear power keeps the Sun from swallowing the planets
# while still preserving size ordering.
BODY_SIZE_POWER = 0.40
BODY_SIZE_COEFF = 0.0115
BODY_DISPLAY_RADIUS_MIN = 1.5
BODY_DISPLAY_RADIUS_MAX = 18.0

# Moons orbit their PARENT, scaled relative to the parent's display radius.
# Real orbit-radius/parent-radius ratios are huge, so they are compressed to
# keep moons near their parent in the solar-system overview.
CHILD_ORBIT_COMPRESSION = 0.12

# Satellites are drawn at (near) true scale relative to their parent so the
# orbit shape (e.g. the Molniya ellipse) is physically meaningful when zoomed in.
SATELLITE_ORBIT_FACTOR = 1.15

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
