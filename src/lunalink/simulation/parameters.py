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
    acquire_threshold_deg: float = None
    drag_cutoff_altitude_m: float = None
    pointing_initial_offset_deg: float = None
    tumble_axis: tuple = None
    pointing_initial_rate_deg_s: tuple = None
    # Slew (rest-to-rest reorientation) scenario
    slew_angle_deg: float = None
    slew_axis: tuple = None
    slew_window_s: float = None
    # Attitude determination (gyro + star tracker + complementary filter)
    estimator_enabled: bool = None
    gyro_bias_deg_hr: tuple = None
    gyro_noise_std_rad_s: float = None
    star_tracker_noise_arcsec: float = None
    star_tracker_interval_s: float = None
    estimator_kp: float = None
    estimator_ki: float = None
    estimator_seed: int = None
    # Central-body environment (the body the satellite orbits). Resolved from the
    # satellite's parent so the simulation works around any planet or moon, not
    # just Earth. Defaults are Earth's values for backward compatibility.
    central_mu: float = None
    central_radius_m: float = None
    central_dipole_tm3: float = None
    central_atmos_rho0: float = None
    central_atmos_ref_alt_m: float = None
    central_atmos_scale_height_m: float = None
    central_solar_flux_scale: float = None   # (1 AU / heliocentric distance)^2
    # Sun-orbit elements of the parent's heliocentric ancestor, used to point the
    # Sun direction from the actual heliocentric position. ``None`` keeps the
    # validated analytic model (for Earth and Earth's moon), so the report is
    # unchanged; set for satellites around other planets.
    central_helio_elements: tuple = None
    central_j2: float = None                 # oblateness coefficient of the parent

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
            # Resolve the central body's physical environment from the parent.
            p.update(resolve_central_body(getattr(satellite, "parent", None)))
        return cls.from_dict(p)


def resolve_central_body(parent_name: str | None) -> dict:
    """Physical environment of the body a satellite orbits, so the simulation is
    correct around any planet or moon (not just Earth).

    Gravitational parameter comes from the built-in table for the known bodies
    (keeping Earth exact) or from ``G*mass`` for a user-added custom body. Radius,
    magnetic dipole and atmosphere come from the body record; a body with no
    dipole and no atmosphere (the default) is treated as field-free and airless.
    """
    from .physics.constants import (
        GM_BODIES, GM_EARTH, R_EARTH_M, GEOMAG_DIPOLE_TM3, G_CONST, AU_M, J2)
    from .repositories.body_repository import BodyRepository

    repo = BodyRepository()
    body = repo.get_by_name(parent_name) if parent_name else None
    if parent_name in GM_BODIES:
        mu = GM_BODIES[parent_name]                       # exact for known bodies
    elif body is not None and body.mass_kg > 0:
        mu = G_CONST * body.mass_kg                        # custom body
    else:
        mu = GM_EARTH
    # Sunlight at the central body's distance from the Sun scales the SRP torque
    # (Phi ~ 1/d^2), so a Mars satellite feels weaker sunlight than an Earth one.
    ancestor = _heliocentric_ancestor(body, repo)
    if ancestor is not None and ancestor.orbit is not None:
        flux_scale = (AU_M / ancestor.orbit.semi_major_axis_m) ** 2
    else:
        flux_scale = 1.0
    # The Sun direction is taken from the ancestor's heliocentric position, except
    # for Earth (and its moon), which keep the validated analytic Sun model.
    helio = None
    if ancestor is not None and ancestor.name != "Earth" and ancestor.orbit is not None:
        o = ancestor.orbit
        helio = (o.semi_major_axis_m, o.eccentricity, o.inclination_deg,
                 o.raan_deg, o.arg_periapsis_deg, o.mean_anomaly_epoch_deg)
    if body is not None:
        return {
            "central_mu": mu,
            "central_radius_m": body.radius_m,
            "central_dipole_tm3": body.magnetic_dipole_tm3,
            "central_atmos_rho0": body.atmosphere_ref_density_kg_m3,
            "central_atmos_ref_alt_m": body.atmosphere_ref_altitude_m,
            "central_atmos_scale_height_m": body.atmosphere_scale_height_m,
            "central_solar_flux_scale": flux_scale,
            "central_helio_elements": helio,
            "central_j2": body.j2,
        }
    # No body record (e.g. tests): fall back to Earth's environment.
    return {
        "central_mu": mu, "central_radius_m": R_EARTH_M,
        "central_dipole_tm3": GEOMAG_DIPOLE_TM3,
        "central_atmos_rho0": 1e-12, "central_atmos_ref_alt_m": 500_000.0,
        "central_atmos_scale_height_m": 60_000.0,
        "central_solar_flux_scale": 1.0, "central_helio_elements": None,
        "central_j2": J2,
    }


def _heliocentric_ancestor(body, repo, _depth: int = 0):
    """Walk up ``body``'s parents to the body that orbits the Sun (so a moon
    resolves to its planet). Returns that body, or ``None`` if not found."""
    if body is None or _depth > 12:
        return None
    if body.parent in (None, "Sun"):
        return body
    return _heliocentric_ancestor(repo.get_by_name(body.parent), repo, _depth + 1)


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
