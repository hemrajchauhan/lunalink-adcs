from dataclasses import dataclass, field
import numpy as np


@dataclass
class OrbitElements:
    """Classical Keplerian elements describing an orbit around a parent body.

    Distances in metres, angles in degrees. ``mean_anomaly_epoch_deg`` is the
    mean anomaly at the simulation epoch (t = 0) and is what makes objects start
    at different points along their orbits.
    """
    semi_major_axis_m: float
    eccentricity: float = 0.0
    inclination_deg: float = 0.0
    raan_deg: float = 0.0                 # right ascension of ascending node
    arg_periapsis_deg: float = 0.0        # argument of periapsis
    mean_anomaly_epoch_deg: float = 0.0

    def to_dict(self) -> dict:
        return {
            "semi_major_axis_m": self.semi_major_axis_m,
            "eccentricity": self.eccentricity,
            "inclination_deg": self.inclination_deg,
            "raan_deg": self.raan_deg,
            "arg_periapsis_deg": self.arg_periapsis_deg,
            "mean_anomaly_epoch_deg": self.mean_anomaly_epoch_deg,
        }

    @staticmethod
    def from_dict(data: dict | None) -> "OrbitElements | None":
        if not data:
            return None
        return OrbitElements(
            semi_major_axis_m=float(data["semi_major_axis_m"]),
            eccentricity=float(data.get("eccentricity", 0.0)),
            inclination_deg=float(data.get("inclination_deg", 0.0)),
            raan_deg=float(data.get("raan_deg", 0.0)),
            arg_periapsis_deg=float(data.get("arg_periapsis_deg", 0.0)),
            mean_anomaly_epoch_deg=float(data.get("mean_anomaly_epoch_deg", 0.0)),
        )


@dataclass
class SpaceObject:
    name: str
    color: str
    # Name of the body this object orbits ("Sun" for planets, None for the Sun).
    parent: str | None = None
    orbit: OrbitElements | None = None
    # Absolute position in the inertial (Sun-centred) frame. Computed by the
    # SolarSystem propagator; cached here for rendering convenience.
    position_m: np.ndarray = field(default_factory=lambda: np.zeros(3))


@dataclass
class CelestialBody(SpaceObject):
    radius_m: float = 1.0
    axial_tilt_deg: float = 0.0
    rotation_period_h: float = 24.0
    has_ring: bool = False
    # Physical properties used by the ADCS simulation when a satellite orbits
    # this body. mass gives the gravitational parameter (mu = G*mass) for custom
    # bodies; a magnetic dipole and an exponential atmosphere drive the magnetic
    # and drag disturbance torques. Defaults model an airless, field-free body.
    mass_kg: float = 0.0
    magnetic_dipole_tm3: float = 0.0
    atmosphere_ref_density_kg_m3: float = 0.0
    atmosphere_ref_altitude_m: float = 0.0
    atmosphere_scale_height_m: float = 60_000.0
    j2: float = 0.0                       # oblateness coefficient (0 = sphere)


@dataclass
class Satellite(SpaceObject):
    mass_kg: float = 1.0
    # (length, width, height) of the spacecraft box
    dimensions_m: np.ndarray = field(default_factory=lambda: np.array([1.0, 1.0, 1.0]))


@dataclass
class Mission:
    """A runnable ADCS scenario: a satellite plus a set of simulation
    parameters (mode, actuators, duration ...). Persisted in missions.json."""
    name: str
    satellite: str
    description: str = ""
    simulation: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {"name": self.name, "satellite": self.satellite,
                "description": self.description, "simulation": dict(self.simulation)}

    @staticmethod
    def from_dict(data: dict) -> "Mission":
        return Mission(
            name=data["name"], satellite=data["satellite"],
            description=data.get("description", ""),
            simulation=dict(data.get("simulation", {})))
