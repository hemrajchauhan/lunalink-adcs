"""Physical and Earth constants (framework Sec. 1, "Mission constants").

These are universal/natural constants, not tunable mission parameters, so they
live in code (one source of truth). Tunable mission, orbit, spacecraft and
simulation parameters live in the JSON data files instead.
"""

# Gravitational parameters mu = G*M  (m^3 / s^2)
GM_SUN = 1.327_124_400_18e20
GM_EARTH = 3.986_004_418e14

# Standard gravitational parameters of the major bodies, so a child orbits its
# parent at a physically sensible rate. Unknown parents fall back to GM_EARTH.
GM_BODIES = {
    "Sun": GM_SUN,
    "Mercury": 2.2032e13,
    "Venus": 3.24859e14,
    "Earth": GM_EARTH,
    "Moon": 4.9048695e12,
    "Mars": 4.282837e13,
    "Jupiter": 1.26686534e17,
    "Saturn": 3.7931187e16,
    "Uranus": 5.793939e15,
    "Neptune": 6.836529e15,
}

# Lengths
AU_M = 1.495_978_707e11          # astronomical unit (m)
R_EARTH_M = 6.378e6              # mean equatorial Earth radius (m)

# Earth / environment
J2 = 1.0826e-3                   # Earth oblateness coefficient
EARTH_ROT_RATE = 7.292e-5        # sidereal rotation rate (rad/s)
OBLIQUITY_DEG = 23.44            # ecliptic obliquity
GEOMAG_DIPOLE_TM3 = 7.94e15      # geomagnetic dipole strength M_B (T m^3)

# Radiation / misc
SOLAR_CONST_W_M2 = 1361.0        # solar constant Phi
LIGHT_SPEED_M_S = 3.0e8          # c
G0 = 9.81                        # standard gravity (m/s^2)
