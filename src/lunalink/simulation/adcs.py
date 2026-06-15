"""LunaLink ADCS simulation - orchestrator (framework Sec. 10 integration loop).

State x = [q (4), omega (3), hw (3)] integrated with RK4 alongside an
analytically propagated orbit. Each step evaluates the environment, the
disturbance torques and the active control law, all imported from the
``physics`` subpackages (one module per group of equations).

Simulation parameters are NOT hard-coded here: defaults come from
``data/simulation_defaults.json`` and are overridden per mission.
"""
from dataclasses import dataclass, field, fields
import numpy as np

from .physics import orbit, attitude, environment, disturbances
from .physics.constants import GM_EARTH, R_EARTH_M, GEOMAG_DIPOLE_TM3
from .physics.dynamics import box_inertia, state_derivative
from .physics.actuators import sizing_summary as _sizing_summary
from .physics.control import (
    bdot_dipole, magnetorquer_torque, auto_gain, pd_gains, pd_torque,
    desaturation_dipole,
)
from .objects import OrbitElements
from .defaults import load_simulation_defaults


@dataclass
class ADCSParams:
    # Spacecraft / mass properties
    mass_kg: float = 500.0
    dims_m: tuple = (2.0, 1.5, 1.0)
    inertia: np.ndarray = None                    # computed from box if None
    # Simulation tunables (defaults overwritten from JSON via from_dict)
    initial_tumble_deg_s: float = 10.0
    rw_max_momentum_nms: float = 4.0
    rw_max_torque_nm: float = 0.05
    magnetorquer_max_dipole_am2: float = 50.0
    residual_dipole_am2: float = 1.0
    srp_area_m2: float = 3.0
    reflectance: float = 0.5
    drag_coeff: float = 2.2
    cp_offset_m: float = 0.1
    natural_freq: float = 0.05
    damping: float = 0.7
    desat_gain: float = 1.0
    detumble_exit_deg_s: float = 1.0
    bdot_gain: float = None                        # auto-sized if None
    mode: str = "detumble"                         # detumble | sun_pointing | full
    # Orbit (Earth-centred); defaults are the LunaLink Molniya HEO
    semi_major_axis_m: float = 24_628_137.0
    eccentricity: float = 0.7207
    inclination_deg: float = 63.4
    raan_deg: float = 0.0
    arg_periapsis_deg: float = 270.0
    mean_anomaly_epoch_deg: float = 0.0
    # Run control
    n_orbits: float = 3.0
    dt_s: float = 8.0

    def get_inertia(self) -> np.ndarray:
        if self.inertia is not None:
            return np.asarray(self.inertia, dtype=float)
        return box_inertia(self.mass_kg, self.dims_m)

    def orbit_elements(self) -> OrbitElements:
        return OrbitElements(self.semi_major_axis_m, self.eccentricity,
                             self.inclination_deg, self.raan_deg,
                             self.arg_periapsis_deg, self.mean_anomaly_epoch_deg)

    @classmethod
    def _field_names(cls):
        return {f.name for f in fields(cls)}

    @classmethod
    def from_dict(cls, params: dict) -> "ADCSParams":
        known = cls._field_names()
        return cls(**{k: v for k, v in params.items() if k in known})

    @classmethod
    def from_mission(cls, satellite, sim_params: dict) -> "ADCSParams":
        """Build params from a satellite (orbit + mass properties) and a
        simulation-parameter dict (defaults merged with mission overrides)."""
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


def default_params(**overrides) -> ADCSParams:
    """ADCSParams seeded from the JSON simulation defaults."""
    params = load_simulation_defaults()
    params.update(overrides)
    return ADCSParams.from_dict(params)


def sizing_summary(params: ADCSParams) -> dict:
    """Actuator sizing for a parameter set (framework Sec. 8)."""
    return _sizing_summary(params.mass_kg, params.dims_m, params.semi_major_axis_m)


def simulate(params: ADCSParams) -> dict:
    I = params.get_inertia()
    elements = params.orbit_elements()
    mu = GM_EARTH
    period_s = orbit.orbital_period_s(params.semi_major_axis_m, mu)
    total_s = params.n_orbits * period_s
    dt = params.dt_s
    steps = int(total_s / dt)

    Kp, Kd = pd_gains(I, params.natural_freq, params.damping)
    D_res = params.residual_dipole_am2 * np.array([1.0, 1.0, 1.0]) / np.sqrt(3)
    cp_offset = np.array([params.cp_offset_m, 0.0, 0.0])

    B_perigee = GEOMAG_DIPOLE_TM3 / (
        params.semi_major_axis_m * (1 - params.eccentricity)) ** 3
    omega0 = np.radians(max(params.initial_tumble_deg_s, 0.5))
    bdot_gain = params.bdot_gain
    if bdot_gain is None:
        bdot_gain = auto_gain(params.magnetorquer_max_dipole_am2, omega0, B_perigee)

    # Initial state per scenario.
    if params.mode == "sun_pointing":
        sun0 = environment.sun_unit_vector(0.0)
        q_cmd0 = attitude.matrix_to_quat(attitude.target_dcm_point_axis(sun0))
        offset = attitude.normalize(np.array([np.sin(np.radians(12.5)), 0.0, 0.0,
                                              np.cos(np.radians(12.5))]))
        q = attitude.normalize(attitude.quat_multiply(q_cmd0, offset))
        omega = np.radians(0.05) * np.array([1.0, -0.5, 0.3])
        mode = "pointing"
    else:
        q = np.array([0.0, 0.0, 0.0, 1.0])
        axis = np.array([1.0, 0.6, -0.3])
        omega = np.radians(params.initial_tumble_deg_s) * axis / np.linalg.norm(axis)
        mode = "detumble"
    hw = np.zeros(3)

    logs = {k: np.zeros(steps) for k in (
        "t_h", "omega_mag", "H_mag", "hw_mag", "att_err",
        "T_gg", "T_srp", "T_mag", "T_aero", "T_dist", "radius_km")}
    omega_hist = np.zeros((steps, 3))
    hw_hist = np.zeros((steps, 3))
    euler_hist = np.zeros((steps, 3))
    eclipse_hist = np.zeros(steps, dtype=bool)
    t_acquire = np.nan

    for k in range(steps):
        t = k * dt
        r, v = orbit.state_vectors_in_parent_frame(elements, mu, t)
        R_norm = np.linalg.norm(r)
        sun = environment.sun_unit_vector(t)
        eclipsed = environment.is_in_eclipse(r, sun)
        B_eci = environment.magnetic_field_eci(r)
        altitude = R_norm - R_EARTH_M
        rho = environment.atmospheric_density(altitude) if altitude < 6.0e5 else 0.0

        R_bi = attitude.quat_to_matrix(q)
        B_body = R_bi @ B_eci

        T_gg = disturbances.gravity_gradient(R_bi, r, I)
        T_srp = disturbances.solar_radiation(R_bi, sun, eclipsed, params.srp_area_m2,
                                             params.reflectance, cp_offset)
        T_mag = disturbances.magnetic(D_res, B_body)
        T_aero = disturbances.aerodynamic(R_bi, v, rho, params.drag_coeff,
                                          params.srp_area_m2, cp_offset)
        T_dist = T_gg + T_srp + T_mag + T_aero

        omega_deg = np.degrees(np.linalg.norm(omega))
        if (params.mode == "full" and mode == "detumble"
                and omega_deg < params.detumble_exit_deg_s):
            mode = "pointing"
            if np.isnan(t_acquire):
                t_acquire = t

        T_mtq = np.zeros(3)
        hw_dot = np.zeros(3)
        if mode == "detumble":
            m = bdot_dipole(omega, B_body, bdot_gain, params.magnetorquer_max_dipole_am2)
            T_mtq = magnetorquer_torque(m, B_body)
        else:
            R_cmd = attitude.target_dcm_point_axis(sun)
            q_cmd = attitude.matrix_to_quat(R_cmd)
            q_e = attitude.quat_error(q_cmd, q)
            Tc = pd_torque(q_e[:3], omega, Kp, Kd)
            hw_dot = np.clip(-Tc, -params.rw_max_torque_nm, params.rw_max_torque_nm)
            if np.linalg.norm(hw) > 0.8 * params.rw_max_momentum_nms:
                m = desaturation_dipole(B_body, hw, params.desat_gain,
                                        params.magnetorquer_max_dipole_am2)
                T_mtq = magnetorquer_torque(m, B_body)

        torque_body = T_dist + T_mtq

        k1q, k1w = state_derivative(q, omega, I, hw, hw_dot, torque_body)
        k2q, k2w = state_derivative(q + 0.5 * dt * k1q, omega + 0.5 * dt * k1w, I, hw, hw_dot, torque_body)
        k3q, k3w = state_derivative(q + 0.5 * dt * k2q, omega + 0.5 * dt * k2w, I, hw, hw_dot, torque_body)
        k4q, k4w = state_derivative(q + dt * k3q, omega + dt * k3w, I, hw, hw_dot, torque_body)
        q = attitude.normalize(q + dt / 6 * (k1q + 2 * k2q + 2 * k3q + k4q))
        omega = omega + dt / 6 * (k1w + 2 * k2w + 2 * k3w + k4w)

        hw = hw + hw_dot * dt
        if mode == "pointing" and np.linalg.norm(hw) > 0.8 * params.rw_max_momentum_nms:
            hw = hw * 0.6
        hw = np.clip(hw, -params.rw_max_momentum_nms, params.rw_max_momentum_nms)

        H = I * omega + hw
        att_err = attitude.pointing_error_deg(q, sun)
        if mode == "pointing" and np.isnan(t_acquire) and att_err < 5.0:
            t_acquire = t

        logs["t_h"][k] = t / 3600.0
        logs["omega_mag"][k] = np.degrees(np.linalg.norm(omega))
        logs["H_mag"][k] = np.linalg.norm(H)
        logs["hw_mag"][k] = np.linalg.norm(hw)
        logs["att_err"][k] = att_err
        logs["T_gg"][k] = np.linalg.norm(T_gg)
        logs["T_srp"][k] = np.linalg.norm(T_srp)
        logs["T_mag"][k] = np.linalg.norm(T_mag)
        logs["T_aero"][k] = np.linalg.norm(T_aero)
        logs["T_dist"][k] = np.linalg.norm(T_dist)
        logs["radius_km"][k] = R_norm / 1000.0
        omega_hist[k] = np.degrees(omega)
        hw_hist[k] = hw
        euler_hist[k] = np.degrees(attitude.quat_to_euler321(q))
        eclipse_hist[k] = eclipsed

    return {
        "t_h": logs["t_h"],
        "omega_deg_s": omega_hist,
        "omega_mag_deg_s": logs["omega_mag"],
        "angular_momentum_nms": logs["H_mag"],
        "wheel_momentum_nms": hw_hist,
        "wheel_momentum_mag_nms": logs["hw_mag"],
        "attitude_error_deg": logs["att_err"],
        "euler_deg": euler_hist,
        "disturbance_nm": logs["T_dist"],
        "T_gg_nm": logs["T_gg"],
        "T_srp_nm": logs["T_srp"],
        "T_mag_nm": logs["T_mag"],
        "T_aero_nm": logs["T_aero"],
        "radius_km": logs["radius_km"],
        "eclipse": eclipse_hist,
        "t_acquire_h": t_acquire / 3600.0 if not np.isnan(t_acquire) else None,
        "period_h": period_s / 3600.0,
        "inertia": I,
    }
