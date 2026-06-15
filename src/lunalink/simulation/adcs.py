"""Full LunaLink ADCS simulation (framework Sec. 10 integration loop).

State x = [q (4), omega (3), hw (3)] integrated with RK4 alongside an
analytically propagated orbit. At each step the environment (Sun, eclipse,
geomagnetic field, density), the disturbance torques (gravity gradient, SRP,
residual magnetic, drag) and the active control law (B-dot detumble, then
quaternion-PD sun-pointing with reaction wheels + magnetic desaturation) are
evaluated, exactly as laid out in the mathematical framework.
"""
from dataclasses import dataclass, field
import numpy as np

from . import orbits, attitude, disturbances, environment
from .objects import OrbitElements
from ..config import GM_EARTH

R_EARTH_M = 6.378e6


def box_inertia(mass_kg: float, dims_m) -> np.ndarray:
    """Principal inertia of a uniform solid box (framework Eq. 16)."""
    ax, ay, az = dims_m
    return mass_kg / 12.0 * np.array([ay ** 2 + az ** 2,
                                      ax ** 2 + az ** 2,
                                      ax ** 2 + ay ** 2])


@dataclass
class ADCSParams:
    # Spacecraft
    mass_kg: float = 500.0
    dims_m: tuple = (2.0, 1.5, 1.0)
    inertia: np.ndarray = None                    # computed from box if None
    # Initial state
    initial_tumble_deg_s: float = 10.0
    # Actuators
    rw_max_momentum_nms: float = 4.0              # h_max per framework sizing
    rw_max_torque_nm: float = 0.05               # tau_max
    magnetorquer_max_dipole_am2: float = 50.0     # m_max
    residual_dipole_am2: float = 1.0              # D
    # Disturbance geometry
    srp_area_m2: float = 3.0
    reflectance: float = 0.5
    drag_coeff: float = 2.2
    cp_offset_m: float = 0.1
    # Control gains
    natural_freq: float = 0.05                    # omega_n (rad/s) for PD
    damping: float = 0.7                          # zeta
    desat_gain: float = 1.0                       # magnetic desaturation gain
    detumble_exit_deg_s: float = 1.0              # switch to pointing below this
    bdot_gain: float = None                       # auto-sized if None
    # Scenario: "detumble" (B-dot only), "sun_pointing" (PD from a detumbled
    # state) or "full" (detumble then auto-switch to pointing).
    mode: str = "detumble"
    # Orbit (Earth-centred); defaults are the LunaLink Molniya HEO
    semi_major_axis_m: float = 24_628_137.0
    eccentricity: float = 0.7207
    inclination_deg: float = 63.4
    raan_deg: float = 0.0
    arg_periapsis_deg: float = 270.0
    mean_anomaly_epoch_deg: float = 0.0
    # Run control
    n_orbits: float = 3.0
    dt_s: float = 8.0                              # ~7 s/run; lower for accuracy

    def get_inertia(self) -> np.ndarray:
        if self.inertia is not None:
            return np.asarray(self.inertia, dtype=float)
        return box_inertia(self.mass_kg, self.dims_m)

    def orbit_elements(self) -> OrbitElements:
        return OrbitElements(self.semi_major_axis_m, self.eccentricity,
                             self.inclination_deg, self.raan_deg,
                             self.arg_periapsis_deg, self.mean_anomaly_epoch_deg)


def _state_derivative(q, omega, I, hw, hw_dot, torque_body):
    """d/dt of [q, omega] for fixed wheel torque/disturbance over the step."""
    H_internal = I * omega + hw
    omega_dot = (torque_body - hw_dot - np.cross(omega, H_internal)) / I
    return attitude.quat_derivative(q, omega), omega_dot


def simulate(params: ADCSParams) -> dict:
    I = params.get_inertia()
    elements = params.orbit_elements()
    mu = GM_EARTH
    period_s = orbits.orbital_period_s(params.semi_major_axis_m, mu)
    total_s = params.n_orbits * period_s
    dt = params.dt_s
    steps = int(total_s / dt)

    # PD gains from natural frequency and damping (framework Eq. 36).
    Kp = I * params.natural_freq ** 2
    Kd = 2 * params.damping * I * params.natural_freq

    # Residual dipole and cp offset directions in body axes.
    D_res = params.residual_dipole_am2 * np.array([1.0, 1.0, 1.0]) / np.sqrt(3)
    cp_offset = np.array([params.cp_offset_m, 0.0, 0.0])

    # Auto-size the B-dot gain so the commanded dipole saturates the
    # magnetorquers near perigee (where the field is strongest).
    B_perigee = environment.GEOMAG_DIPOLE_TM3 / (
        params.semi_major_axis_m * (1 - params.eccentricity)) ** 3
    omega0 = np.radians(max(params.initial_tumble_deg_s, 0.5))
    bdot_gain = params.bdot_gain
    if bdot_gain is None:
        bdot_gain = 0.5 * params.magnetorquer_max_dipole_am2 / (omega0 * B_perigee)

    # Initial state depends on the scenario.
    if params.mode == "sun_pointing":
        # Start detumbled and ~25 deg off the Sun line, so the wheels acquire
        # with a modest slew and we then watch disturbance-driven momentum
        # build up and desaturate.
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
        r, v = orbits.state_vectors_in_parent_frame(elements, mu, t)
        R_norm = np.linalg.norm(r)
        sun = environment.sun_unit_vector(t)
        eclipsed = environment.is_in_eclipse(r, sun)
        B_eci = environment.magnetic_field_eci(r)
        altitude = R_norm - R_EARTH_M
        rho = environment.atmospheric_density(altitude) if altitude < 6.0e5 else 0.0

        R_bi = attitude.quat_to_matrix(q)
        B_body = R_bi @ B_eci

        # Disturbance torques (body frame).
        T_gg = disturbances.gravity_gradient(R_bi, r, I)
        T_srp = disturbances.solar_radiation(R_bi, sun, eclipsed, params.srp_area_m2,
                                             params.reflectance, cp_offset)
        T_mag = disturbances.magnetic(D_res, B_body)
        T_aero = disturbances.aerodynamic(R_bi, v, rho, params.drag_coeff,
                                          params.srp_area_m2, cp_offset)
        T_dist = T_gg + T_srp + T_mag + T_aero

        # In "full" scenario, hand over from detumble to pointing once the
        # rates are low enough for the wheels to take control.
        omega_deg = np.degrees(np.linalg.norm(omega))
        if (params.mode == "full" and mode == "detumble"
                and omega_deg < params.detumble_exit_deg_s):
            mode = "pointing"
            if np.isnan(t_acquire):
                t_acquire = t

        T_mtq = np.zeros(3)
        hw_dot = np.zeros(3)

        if mode == "detumble":
            # B-dot: m = k (omega x B); torque T = m x B (framework Eq. 33).
            m = bdot_gain * np.cross(omega, B_body)
            m = np.clip(m, -params.magnetorquer_max_dipole_am2,
                        params.magnetorquer_max_dipole_am2)
            T_mtq = np.cross(m, B_body)
        else:
            # Quaternion-PD sun-pointing with reaction wheels (Eq. 35).
            R_cmd = attitude.target_dcm_point_axis(sun)
            q_cmd = attitude.matrix_to_quat(R_cmd)
            q_e = attitude.quat_error(q_cmd, q)
            Tc = -Kp * q_e[:3] - Kd * omega
            hw_dot = np.clip(-Tc, -params.rw_max_torque_nm, params.rw_max_torque_nm)
            # Magnetic desaturation when wheels approach saturation (Eq. 37).
            if np.linalg.norm(hw) > 0.8 * params.rw_max_momentum_nms:
                B2 = B_body @ B_body
                if B2 > 0:
                    m = params.desat_gain / B2 * np.cross(B_body, hw)
                    m = np.clip(m, -params.magnetorquer_max_dipole_am2,
                                params.magnetorquer_max_dipole_am2)
                    T_mtq = np.cross(m, B_body)

        torque_body = T_dist + T_mtq

        # RK4 on [q, omega] with control/disturbance held over the step.
        k1q, k1w = _state_derivative(q, omega, I, hw, hw_dot, torque_body)
        k2q, k2w = _state_derivative(q + 0.5 * dt * k1q, omega + 0.5 * dt * k1w, I, hw, hw_dot, torque_body)
        k3q, k3w = _state_derivative(q + 0.5 * dt * k2q, omega + 0.5 * dt * k2w, I, hw, hw_dot, torque_body)
        k4q, k4w = _state_derivative(q + dt * k3q, omega + dt * k3w, I, hw, hw_dot, torque_body)
        q = attitude.normalize(q + dt / 6 * (k1q + 2 * k2q + 2 * k3q + k4q))
        omega = omega + dt / 6 * (k1w + 2 * k2w + 2 * k3w + k4w)

        # Wheel momentum integration with saturation; desaturation bleeds it.
        hw = hw + hw_dot * dt
        if mode == "pointing" and np.linalg.norm(hw) > 0.8 * params.rw_max_momentum_nms:
            hw = hw * 0.6                       # momentum dump effect
        hw = np.clip(hw, -params.rw_max_momentum_nms, params.rw_max_momentum_nms)

        # Logging.
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


def sizing_summary(params: ADCSParams) -> dict:
    """Actuator sizing hand-calcs (framework Sec. 8) for the report."""
    I = params.get_inertia()
    period_s = orbits.orbital_period_s(params.semi_major_axis_m, mu := GM_EARTH)
    # Slew sizing: 90 deg rest-to-rest in 5 min about the max-inertia axis.
    theta = np.pi / 2
    t_slew = 300.0
    I_max = I.max()
    T_slew = 4 * I_max * theta / t_slew ** 2
    h_slew = T_slew * t_slew / 2
    # Cyclic storage from SRP at apogee.
    T_d = 3.3e-6
    h_store = T_d * period_s / 4 * 0.707
    return {
        "inertia_kgm2": I,
        "slew_torque_nm": T_slew,
        "slew_momentum_nms": h_slew,
        "cyclic_storage_nms": h_store,
        "recommended_wheel_hmax_nms": max(h_slew, h_store) * 1.5,
    }
