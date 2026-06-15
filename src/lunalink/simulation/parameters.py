"""ADCS simulation parameters.

``ADCSParams`` is a pure container - it carries NO hard-coded values. Every
value is supplied from the JSON data files: simulation tunables and algorithm
constants from ``simulation_defaults.json`` (merged with a mission's overrides),
and mass / orbit from the selected satellite (``satellites.json``).
"""
from dataclasses import dataclass, fields
import numpy as np

from .objects import OrbitElements
from .defaults import load_simulation_defaults
from .physics.dynamics import box_inertia


@dataclass
class ADCSParams:
    # Spacecraft / mass properties (from the satellite)
    mass_kg: float = None
    dims_m: tuple = None
    inertia: np.ndarray = None
    # Orbit (from the satellite)
    semi_major_axis_m: float = None
    eccentricity: float = None
    inclination_deg: float = None
    raan_deg: float = None
    arg_periapsis_deg: float = None
    mean_anomaly_epoch_deg: float = None
    # Simulation tunables (from simulation_defaults.json / mission overrides)
    mode: str = None
    n_orbits: float = None
    dt_s: float = None
    initial_tumble_deg_s: float = None
    rw_max_momentum_nms: float = None
    rw_max_torque_nm: float = None
    magnetorquer_max_dipole_am2: float = None
    residual_dipole_am2: float = None
    srp_area_m2: float = None
    reflectance: float = None
    drag_coeff: float = None
    cp_offset_m: float = None
    natural_freq: float = None
    damping: float = None
    desat_gain: float = None
    detumble_exit_deg_s: float = None
    bdot_gain: float = None                 # explicit gain; auto-sized if None
    # Algorithm / solver constants (also data, not magic numbers)
    bdot_gain_fraction: float = None
    desat_trigger_fraction: float = None
    momentum_dump_factor: float = None
    acquire_threshold_deg: float = None
    drag_cutoff_altitude_m: float = None
    pointing_initial_offset_deg: float = None
    tumble_axis: tuple = None
    pointing_initial_rate_deg_s: tuple = None

    # -- derived --------------------------------------------------------
    def get_inertia(self) -> np.ndarray:
        if self.inertia is not None:
            return np.asarray(self.inertia, dtype=float)
        return box_inertia(self.mass_kg, self.dims_m)

    def orbit_elements(self) -> OrbitElements:
        return OrbitElements(self.semi_major_axis_m, self.eccentricity,
                             self.inclination_deg, self.raan_deg,
                             self.arg_periapsis_deg, self.mean_anomaly_epoch_deg)

    # -- builders -------------------------------------------------------
    @classmethod
    def _field_names(cls):
        return {f.name for f in fields(cls)}

    @classmethod
    def from_dict(cls, params: dict) -> "ADCSParams":
        known = cls._field_names()
        return cls(**{k: v for k, v in params.items() if k in known})

    @classmethod
    def from_mission(cls, satellite, sim_params: dict) -> "ADCSParams":
        """Build from a satellite (mass + orbit) and a simulation-parameter dict
        (already merged with the JSON defaults)."""
        p = dict(sim_params)
        if satellite is not None:
            p["mass_kg"] = satellite.mass_kg
            p["dims_m"] = tuple(np.asarray(satellite.dimensions_m, dtype=float))
            p["inertia"] = box_inertia(satellite.mass_kg, p["dims_m"])
            o = satellite.orbit
            if o is not None:
                p.update(semi_major_axis_m=o.semi_major_axis_m,
                         eccentricity=o.eccentricity,
                         inclination_deg=o.inclination_deg, raan_deg=o.raan_deg,
                         arg_periapsis_deg=o.arg_periapsis_deg,
                         mean_anomaly_epoch_deg=o.mean_anomaly_epoch_deg)
        return cls.from_dict(p)


def default_params(satellite_name: str = None, **overrides) -> ADCSParams:
    """ADCSParams seeded from the JSON defaults and a reference satellite.

    The reference satellite is taken from ``simulation_defaults.json``
    (``reference_satellite``) unless one is passed explicitly.
    """
    from .repositories.satellite_repository import SatelliteRepository

    params = load_simulation_defaults()
    params.update(overrides)
    name = satellite_name or params.get("reference_satellite")
    repo = SatelliteRepository()
    satellite = repo.get_by_name(name) if name else None
    if satellite is None:
        all_sats = repo.load_all()
        if not all_sats:
            raise ValueError("No satellite available to seed default ADCS params.")
        satellite = all_sats[0]
    return ADCSParams.from_mission(satellite, params)
