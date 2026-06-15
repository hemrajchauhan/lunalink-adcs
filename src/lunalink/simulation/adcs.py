"""Lightweight ADCS simulation for the LunaLink spacecraft.

Two operating phases are modelled:

  1. Detumbling - a B-dot magnetorquer law removes the initial body rates. The
     resulting body-rate magnitude decays near-exponentially with a time
     constant set by the magnetorquer authority and the spacecraft inertia
     (the standard textbook B-dot behaviour); a small nutation oscillation is
     superimposed so all three axes are visible.
  2. Sun-pointing - reaction wheels hold attitude (the pointing error relaxes
     with a PD time constant) and absorb the secular disturbance torque. Their
     stored momentum therefore ramps up until a magnetorquer "momentum dump"
     desaturates them, producing the characteristic saw-tooth.

The disturbance torque is tied to orbit position: gravity gradient and the
residual magnetic dipole both scale as 1/r^3, so they peak sharply at the HEO
perigee. All maths is plain, vectorised NumPy - fully testable headless.
"""
from dataclasses import dataclass, field
import numpy as np

from .orbits import solve_kepler, mean_motion
from ..config import GM_EARTH


@dataclass
class ADCSParams:
    inertia: np.ndarray = field(
        default_factory=lambda: np.array([180.0, 200.0, 150.0]))  # kg m^2 (Ix,Iy,Iz)
    initial_tumble_deg_s: float = 10.0                # deg/s tumble magnitude
    rw_max_momentum_nms: float = 12.0                 # per-wheel storage
    magnetorquer_dipole_am2: float = 30.0             # A m^2
    detumble_efficiency: float = 0.02                 # B-dot effectiveness factor
    pointing_settle_frac: float = 0.06                # PD settle time / orbit period
    momentum_buildup_scale: float = 60.0              # disturbance -> wheel Nms
    semi_major_axis_m: float = 24_628_137.0
    eccentricity: float = 0.7207
    n_orbits: float = 3.0
    orbital_period_h: float = 12.0
    dt_s: float = 15.0


def _radius(time_s, a, e):
    """Geocentric distance (m) along the orbit, measured from perigee."""
    M = mean_motion(a, GM_EARTH) * np.atleast_1d(time_s)
    E = np.array([solve_kepler(m, e) for m in M])
    return a * (1 - e * np.cos(E))


def simulate(params: ADCSParams) -> dict:
    I = np.asarray(params.inertia, dtype=float)
    period_s = params.orbital_period_h * 3600.0
    total_s = params.n_orbits * period_s
    dt = params.dt_s
    t = np.arange(0.0, total_s, dt)

    # --- orbit-driven disturbance environment ---------------------------
    r = _radius(t, params.semi_major_axis_m, params.eccentricity)
    r_perigee = params.semi_major_axis_m * (1 - params.eccentricity)
    B = 3.0e-5 * (r_perigee / r) ** 3                      # dipole field proxy (T)
    gravity_gradient = 3.0 * GM_EARTH / r ** 3 * abs(I[2] - I[0]) * 0.5
    srp_bias = 2.0e-6
    disturbance = gravity_gradient + params.magnetorquer_dipole_am2 * 0.02 * B + srp_bias

    # --- phase 1: detumbling (B-dot exponential decay) ------------------
    omega0 = np.radians(params.initial_tumble_deg_s)
    bdot_torque = params.magnetorquer_dipole_am2 * np.mean(B)          # ~Nm
    tau_detumble = (np.mean(I) * omega0 / bdot_torque) * params.detumble_efficiency
    rate_env = omega0 * np.exp(-t / tau_detumble)                      # rad/s envelope

    # Superimpose a bounded nutation so each axis is distinguishable.
    nut = 2 * np.pi / (0.04 * period_s)
    u = np.stack([np.cos(nut * t),
                  0.8 * np.sin(nut * t),
                  0.5 * np.cos(2 * nut * t + 0.7)], axis=1)
    u /= np.linalg.norm(u, axis=1, keepdims=True)
    omega = rate_env[:, None] * u                                     # rad/s, 3-axis
    omega_mag = rate_env

    # Time at which the spacecraft is considered detumbled (< 0.5 deg/s).
    target = np.radians(0.5)
    t_acquire = tau_detumble * np.log(max(omega0 / target, 1.0))

    # --- phase 2: sun-pointing -----------------------------------------
    pointing = np.where(
        t >= t_acquire,
        120.0 * np.exp(-(t - t_acquire) / (params.pointing_settle_frac * period_s)),
        120.0)
    attitude_error = pointing + np.degrees(omega_mag) * 0.5 + 0.05

    # Reaction wheels engage only after acquisition and integrate the secular
    # disturbance; a momentum dump resets them near capacity (saw-tooth).
    pointing_mask = t >= t_acquire
    secular = disturbance * pointing_mask * params.momentum_buildup_scale
    h_raw = np.cumsum(secular * dt)
    desat = 0.8 * params.rw_max_momentum_nms
    wheel_mag = np.where(desat > 0, np.mod(h_raw, desat), 0.0) * pointing_mask
    # Distribute stored momentum across three wheels for the per-axis view.
    wheel = wheel_mag[:, None] * np.array([0.6, 0.5, 0.62])

    return {
        "t_h": t / 3600.0,
        "omega_deg_s": np.degrees(omega),
        "omega_mag_deg_s": np.degrees(omega_mag),
        "wheel_momentum_nms": wheel,
        "wheel_momentum_mag_nms": wheel_mag,
        "attitude_error_deg": attitude_error,
        "disturbance_nm": disturbance,
        "radius_km": r / 1000.0,
        "t_acquire_h": t_acquire / 3600.0,
    }
