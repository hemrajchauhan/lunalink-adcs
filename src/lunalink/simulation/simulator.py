"""ADCS integration loop (framework Sec. 10).

State x = [q (4), omega (3), hw (3)] advanced with RK4 alongside the
analytically propagated orbit. Each step evaluates the environment, the
disturbance torques and the active control law from the ``physics`` package.
All numeric constants come from the parameter set (sourced from JSON), so this
file contains no tuning magic numbers.
"""
import numpy as np

from .physics import orbit, attitude, environment, disturbances, determination
from .physics.constants import GM_EARTH, R_EARTH_M, GEOMAG_DIPOLE_TM3
from .physics.dynamics import state_derivative
from .physics.actuators import sizing_summary as _sizing_summary
from .physics.control import (
    bdot_dipole, magnetorquer_torque, auto_gain, pd_gains, pd_torque,
    desaturation_dipole,
)
from .parameters import ADCSParams
from . import analysis


def sizing_summary(params: ADCSParams) -> dict:
    """Actuator sizing for a parameter set (framework Sec. 8)."""
    kwargs = {}
    if params.slew_angle_deg is not None:
        kwargs["slew_angle_deg"] = params.slew_angle_deg
    return _sizing_summary(params.mass_kg, params.dims_m,
                           params.semi_major_axis_m, **kwargs)


def _initial_state(params, I):
    """Return (q, omega, mode) for the chosen scenario."""
    if params.mode == "sun_pointing":
        sun0 = environment.sun_unit_vector(0.0)
        q_cmd0 = attitude.matrix_to_quat(attitude.target_dcm_point_axis(sun0))
        half = 0.5 * np.radians(params.pointing_initial_offset_deg)   # quaternion half-angle
        offset = attitude.normalize(np.array([np.sin(half), 0.0, 0.0, np.cos(half)]))
        q = attitude.normalize(attitude.quat_multiply(q_cmd0, offset))
        omega = np.radians(np.asarray(params.pointing_initial_rate_deg_s, dtype=float))
        return q, omega, "pointing"
    if params.mode == "slew":
        # Rest-to-rest reorientation: start at rest, aligned with the inertial
        # frame; the controller drives the body to the commanded attitude.
        return np.array([0.0, 0.0, 0.0, 1.0]), np.zeros(3), "slew"
    q = np.array([0.0, 0.0, 0.0, 1.0])
    axis = np.asarray(params.tumble_axis, dtype=float)
    omega = np.radians(params.initial_tumble_deg_s) * axis / np.linalg.norm(axis)
    return q, omega, "detumble"


def _slew_estimate(params: ADCSParams, inertia: np.ndarray, axis: np.ndarray) -> dict:
    """Bang-bang slew time t = 2 sqrt(theta/alpha) and a momentum-limit check
    (framework Eq. 29). ``inertia`` is the diagonal principal tensor."""
    axis = axis / np.linalg.norm(axis)
    inertia_axis = float(axis @ (inertia * axis))      # inertia about slew axis
    theta = np.radians(params.slew_angle_deg)
    alpha = params.rw_max_torque_nm / inertia_axis      # max angular accel
    t_bb = 2.0 * np.sqrt(theta / alpha)
    peak_momentum = np.sqrt(theta * inertia_axis * params.rw_max_torque_nm)
    return {
        "inertia_axis_kgm2": inertia_axis,
        "bang_bang_time_s": t_bb,
        "peak_momentum_nms": peak_momentum,
        "momentum_limited": bool(peak_momentum > params.rw_max_momentum_nms),
    }


def _environment_at(elements, mu: float, params: ADCSParams, t: float) -> dict:
    """Orbit state and environment fields at simulation time ``t`` (inertial
    frame): position/velocity, Sun direction, eclipse flag, geomagnetic field
    and atmospheric density (zero above the drag cut-off altitude)."""
    r, v = orbit.state_vectors_in_parent_frame(elements, mu, t)
    sun = environment.sun_unit_vector(t)
    altitude = np.linalg.norm(r) - R_EARTH_M
    return {
        "r": r,
        "v": v,
        "sun": sun,
        "eclipsed": environment.is_in_eclipse(r, sun),
        "B_eci": environment.magnetic_field_eci(r),
        "rho": (environment.atmospheric_density(altitude)
                if altitude < params.drag_cutoff_altitude_m else 0.0),
    }


def _disturbance_torques(env: dict, R_bi: np.ndarray, B_body: np.ndarray,
                         I: np.ndarray, params: ADCSParams,
                         D_res: np.ndarray, cp_offset: np.ndarray) -> dict:
    """All four disturbance torques (body frame, N m) plus their sum."""
    torques = {
        "gg": disturbances.gravity_gradient(R_bi, env["r"], I),
        "srp": disturbances.solar_radiation(
            R_bi, env["sun"], env["eclipsed"], params.srp_area_m2,
            params.reflectance, cp_offset),
        "mag": disturbances.magnetic(D_res, B_body),
        "aero": disturbances.aerodynamic(
            R_bi, env["v"], env["rho"], params.drag_coeff,
            params.srp_area_m2, cp_offset),
    }
    torques["total"] = torques["gg"] + torques["srp"] + torques["mag"] + torques["aero"]
    return torques


def simulate(params: ADCSParams) -> dict:
    I = params.get_inertia()
    elements = params.orbit_elements()
    mu = GM_EARTH
    period_s = orbit.orbital_period_s(params.semi_major_axis_m, mu)

    is_slew = params.mode == "slew"
    if is_slew:
        # A slew is a short event (minutes); run a fixed window with a fine step
        # so the accelerate/coast/decelerate profile is well resolved.
        total_s = params.slew_window_s
        dt = min(params.dt_s, 2.0)
        slew_axis = np.asarray(params.slew_axis, dtype=float)
        q_slew_target = attitude.quat_from_axis_angle(
            slew_axis, np.radians(params.slew_angle_deg))
        slew = _slew_estimate(params, I, slew_axis)
    else:
        total_s = params.n_orbits * period_s
        dt = params.dt_s
        q_slew_target = None
        slew = None
    steps = int(total_s / dt)

    Kp, Kd = pd_gains(I, params.natural_freq, params.damping)
    D_res = params.residual_dipole_am2 * np.array([1.0, 1.0, 1.0]) / np.sqrt(3)
    cp_offset = np.array([params.cp_offset_m, 0.0, 0.0])
    desat_level = params.desat_trigger_fraction * params.rw_max_momentum_nms

    # Auto-size the B-dot gain to saturate the magnetorquers near perigee.
    B_perigee = GEOMAG_DIPOLE_TM3 / (
        params.semi_major_axis_m * (1 - params.eccentricity)) ** 3
    omega0 = np.radians(max(params.initial_tumble_deg_s, 0.5))
    bdot_gain = params.bdot_gain
    if bdot_gain is None:
        bdot_gain = auto_gain(params.magnetorquer_max_dipole_am2, omega0, B_perigee,
                              fraction=params.bdot_gain_fraction)

    q, omega, mode = _initial_state(params, I)
    hw = np.zeros(3)

    logs = {k: np.zeros(steps) for k in (
        "t_h", "omega_mag", "H_mag", "hw_mag", "att_err",
        "T_gg", "T_srp", "T_mag", "T_aero", "T_dist", "radius_km",
        "know_err", "b_hat_err")}

    # Attitude determination: gyro (biased+noisy) + star tracker, fused by a
    # complementary filter. Runs in parallel with the truth state so we can plot
    # knowledge error (estimate vs truth) separately from control error.
    est_on = bool(params.estimator_enabled)
    if est_on:
        rng = np.random.default_rng(params.estimator_seed)
        b_true = (np.asarray(params.gyro_bias_deg_hr, dtype=float)
                  * determination.DEG_PER_HR_TO_RAD_S)
        gyro_noise = params.gyro_noise_std_rad_s
        st_noise = params.star_tracker_noise_arcsec * determination.ARCSEC_TO_RAD
        st_every = max(1, int(round(params.star_tracker_interval_s / dt)))
        st_interval = st_every * dt
        q_hat = q.copy()
        b_hat = np.zeros(3)
    omega_hist = np.zeros((steps, 3))
    hw_hist = np.zeros((steps, 3))
    euler_hist = np.zeros((steps, 3))
    quat_hist = np.zeros((steps, 4))    # attitude history for the 3D view
    eclipse_hist = np.zeros(steps, dtype=bool)
    t_acquire = np.nan

    # Cumulative disturbance angular momentum H = integral(T dt), body frame,
    # for the momentum budget and the secular/cyclic classification.
    dist_mom = np.zeros((steps, 3))
    src_mom = {k: np.zeros((steps, 3)) for k in ("gg", "srp", "mag", "aero")}
    accum = np.zeros(3)
    src_accum = {k: np.zeros(3) for k in src_mom}

    for k in range(steps):
        t = k * dt
        env = _environment_at(elements, mu, params, t)
        r, sun, eclipsed = env["r"], env["sun"], env["eclipsed"]
        R_norm = np.linalg.norm(r)

        R_bi = attitude.quat_to_matrix(q)
        B_body = R_bi @ env["B_eci"]

        torques = _disturbance_torques(env, R_bi, B_body, I, params,
                                       D_res, cp_offset)
        T_gg, T_srp = torques["gg"], torques["srp"]
        T_mag, T_aero = torques["mag"], torques["aero"]
        T_dist = torques["total"]

        # Integrate disturbance torque -> disturbance angular momentum demand.
        accum = accum + T_dist * dt
        dist_mom[k] = accum
        for key, torque in (("gg", T_gg), ("srp", T_srp), ("mag", T_mag), ("aero", T_aero)):
            src_accum[key] = src_accum[key] + torque * dt
            src_mom[key][k] = src_accum[key]

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
            # Quaternion-PD to the commanded attitude (Sun line for pointing,
            # the slew target for slew). Shortest-path error (q and -q are the
            # same rotation).
            if mode == "slew":
                q_cmd = q_slew_target
            else:
                q_cmd = attitude.matrix_to_quat(attitude.target_dcm_point_axis(sun))
            q_e = attitude.quat_error(q_cmd, q)
            if q_e[3] < 0:
                q_e = -q_e
            Tc = pd_torque(q_e[:3], omega, Kp, Kd)
            hw_dot = np.clip(-Tc, -params.rw_max_torque_nm, params.rw_max_torque_nm)
            # Wheel saturation: a full wheel cannot absorb further momentum, so
            # the achievable hw_dot is whatever keeps hw within capacity. Using
            # this *actual* hw_dot in the dynamics keeps the reaction torque on
            # the body consistent with the momentum the wheels really exchange.
            hw_next = np.clip(hw + hw_dot * dt,
                              -params.rw_max_momentum_nms, params.rw_max_momentum_nms)
            hw_dot = (hw_next - hw) / dt
            # Magnetic desaturation only in steady pointing - never mid-slew,
            # where the high wheel momentum is intentional and is returned at the
            # end of the manoeuvre.
            if mode == "pointing" and np.linalg.norm(hw) > desat_level:
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

        # Determination: propagate the estimate with the gyro, reset on star fixes.
        if est_on:
            w_meas = determination.gyro_measurement(omega, b_true, gyro_noise, rng)
            q_hat = determination.propagate_estimate(q_hat, w_meas - b_hat, dt)
            if k % st_every == 0:
                q_meas = determination.star_tracker_measurement(q, st_noise, rng)
                q_hat, b_hat, _ = determination.star_update(
                    q_hat, b_hat, q_meas, params.estimator_kp,
                    params.estimator_ki, st_interval,
                    expected_rotation_rad=float(
                        np.linalg.norm(w_meas - b_hat) * st_interval))
            logs["know_err"][k] = determination.knowledge_error_deg(q_hat, q)
            logs["b_hat_err"][k] = (np.linalg.norm(b_hat - b_true)
                                    / determination.DEG_PER_HR_TO_RAD_S)

        # Wheel momentum integrates the (already saturation-limited) wheel
        # torque. Momentum is only ever *removed* by the magnetic desaturation
        # torque above; an instantaneous, torque-free dump would violate
        # conservation of angular momentum.
        hw = hw + hw_dot * dt

        H = I * omega + hw
        if mode == "slew":
            # Error = rotation angle from the current to the commanded attitude.
            q_e = attitude.quat_error(q_slew_target, q)
            att_err = float(np.degrees(2.0 * np.arccos(np.clip(abs(q_e[3]), -1.0, 1.0))))
        else:
            att_err = attitude.pointing_error_deg(q, sun)
        if np.isnan(t_acquire) and mode in ("pointing", "slew") \
                and att_err < params.acquire_threshold_deg:
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
        quat_hist[k] = q
        eclipse_hist[k] = eclipsed

    # Momentum budget + disturbance hierarchy (lecture Part 3).
    t_s = logs["t_h"] * 3600.0
    budget = analysis.momentum_budget(t_s, dist_mom, period_s, B_perigee)
    # The wheels must store the larger of the cyclic disturbance swing and the
    # slew demand; for LunaLink the slew dominates (vs the lecture's AI1, where
    # the cyclic swing dominated). Fold the slew requirement in here.
    if budget:
        slew_momentum = sizing_summary(params)["slew_momentum_nms"]
        budget["slew_momentum_nms"] = slew_momentum
        budget["slew_angle_deg"] = params.slew_angle_deg
        budget["recommended_wheel_hmax_nms"] = 1.5 * max(
            budget["cyclic_swing_nms"], slew_momentum)
    hierarchy = analysis.disturbance_hierarchy(
        {"Gravity gradient": logs["T_gg"], "Solar pressure": logs["T_srp"],
         "Magnetic": logs["T_mag"], "Aerodynamic": logs["T_aero"]},
        {"Gravity gradient": src_mom["gg"], "Solar pressure": src_mom["srp"],
         "Magnetic": src_mom["mag"], "Aerodynamic": src_mom["aero"]},
        t_s, logs["radius_km"], period_s)

    # J2 secular drift rates: justify the fixed-Keplerian-orbit assumption.
    j2_rates = orbit.j2_secular_rates(
        params.semi_major_axis_m, params.eccentricity, params.inclination_deg, mu)
    j2_rates["drift_over_run"] = orbit.drift_over_window(j2_rates, total_s)

    # Determination / pointing budget: knowledge error (estimate vs truth) vs
    # control error (truth vs command), evaluated over the converged tail of the
    # run, compared with the lecture's 0.1° = 0.01° + 0.08° + 0.01° split.
    determ = None
    if est_on and steps > 0:
        tail = slice(max(0, steps - steps // 4), steps)
        know = logs["know_err"][tail]
        ctrl = logs["att_err"][tail]
        know_rms = float(np.sqrt(np.mean(know ** 2)))
        ctrl_rms = float(np.sqrt(np.mean(ctrl ** 2)))
        determ = {
            "knowledge_rms_deg": know_rms,
            "knowledge_peak_deg": float(np.max(know)),
            "control_rms_deg": ctrl_rms,
            "pointing_total_deg": know_rms + ctrl_rms,
            "bias_initial_deg_hr": float(np.linalg.norm(b_true)
                                         / determination.DEG_PER_HR_TO_RAD_S),
            "bias_final_deg_hr": float(logs["b_hat_err"][-1]),
            "star_tracker_noise_deg": float(params.star_tracker_noise_arcsec
                                            * determination.ARCSEC_TO_RAD * 180.0 / np.pi),
            "knowledge_budget_deg": 0.01,
            "control_budget_deg": 0.08,
            "total_budget_deg": 0.10,
        }

    if is_slew and slew is not None:
        slew["settle_time_s"] = None if np.isnan(t_acquire) else float(t_acquire)
        slew["peak_rate_deg_s"] = float(np.max(logs["omega_mag"]))
        slew["peak_wheel_nms"] = float(np.max(logs["hw_mag"]))
        slew["angle_deg"] = params.slew_angle_deg

    return {
        "mode": params.mode,
        "rw_capacity_nms": params.rw_max_momentum_nms,
        "desat_trigger_nms": desat_level,
        "acquire_threshold_deg": params.acquire_threshold_deg,
        "t_h": logs["t_h"],
        "omega_deg_s": omega_hist,
        "omega_mag_deg_s": logs["omega_mag"],
        "angular_momentum_nms": logs["H_mag"],
        "wheel_momentum_nms": hw_hist,
        "wheel_momentum_mag_nms": logs["hw_mag"],
        "attitude_error_deg": logs["att_err"],
        "euler_deg": euler_hist,
        "quaternion": quat_hist,
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
        "dist_momentum_nms": np.linalg.norm(dist_mom, axis=1),
        "momentum_budget": budget,
        "disturbance_hierarchy": hierarchy,
        "slew": slew,
        "j2_secular": j2_rates,
        "determination": determ,
        "knowledge_error_deg": logs["know_err"],
        "gyro_bias_error_deg_hr": logs["b_hat_err"],
    }
