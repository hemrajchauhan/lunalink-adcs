"""Post-processing of a simulation run: the momentum budget and the
disturbance hierarchy (lecture "The Pointing Problem", Part 3).

The two design-driving numbers (lecture slides 28-29):

  * CYCLIC swing per orbit  -> sizes what must STORE momentum (reaction wheels).
    A cyclic torque integrates to ~zero each orbit; it is borrowed and returned.
  * SECULAR momentum per day -> sizes what must REMOVE momentum (magnetorquers).
    A secular torque never averages out; it must be dumped against the field.

Both come from integrating the disturbance torque into a disturbance angular
momentum  H_dist(t) = integral( T_dist dt )  and separating its secular part
(the net drift over COMPLETE orbits, where the cyclic part cancels exactly)
from its cyclic part (the peak excursion about that secular trend).
"""
import numpy as np

SECONDS_PER_DAY = 86400.0


def _secular_and_cyclic(t_s: np.ndarray, H: np.ndarray, period_s: float):
    """Return (secular_per_orbit_vec, cyclic_swing).

    Secular is the net momentum over an integer number of orbits (cyclic torque
    integrates to zero over a full orbit, so it cancels). Cyclic is the peak
    excursion about the resulting secular ramp.
    """
    n_orbits = int(t_s[-1] // period_s)
    if n_orbits >= 1:
        idx_end = int(np.argmin(np.abs(t_s - n_orbits * period_s)))
        secular_per_orbit = (H[idx_end] - H[0]) / n_orbits
    else:                                   # less than one orbit: use endpoints
        secular_per_orbit = (H[-1] - H[0]) * (period_s / max(t_s[-1], 1.0))
    trend = H[0] + np.outer(t_s / period_s, secular_per_orbit)
    cyclic_swing = float(np.max(np.linalg.norm(H - trend, axis=1)))
    return secular_per_orbit, cyclic_swing


def momentum_budget(t_s: np.ndarray, H_dist: np.ndarray, period_s: float,
                    field_perigee_t: float, margin: float = 1.5) -> dict:
    """Cyclic / secular split of the disturbance angular momentum demand.

    H_dist is the cumulative integral of the disturbance torque (N m s, body
    frame). ``field_perigee_t`` is |B| at perigee, used for a best-case dump
    dipole estimate (D = T / B).
    """
    t_s = np.asarray(t_s, dtype=float)
    H = np.asarray(H_dist, dtype=float)
    if H.shape[0] < 2:
        return {}

    secular_per_orbit, cyclic_swing = _secular_and_cyclic(t_s, H, period_s)
    secular_torque = float(np.linalg.norm(secular_per_orbit) / period_s)  # N m
    dump_dipole = secular_torque / field_perigee_t if field_perigee_t > 0 else float("inf")
    return {
        "cyclic_swing_nms": cyclic_swing,
        "secular_torque_nm": secular_torque,
        "secular_per_orbit_nms": float(np.linalg.norm(secular_per_orbit)),
        "secular_per_day_nms": secular_torque * SECONDS_PER_DAY,
        "storage_required_nms": cyclic_swing,
        "recommended_wheel_hmax_nms": cyclic_swing * margin,
        "dump_dipole_am2": dump_dipole,                     # lower bound (T perp B)
    }


def disturbance_hierarchy(sources_mag: dict, sources_mom: dict, t_s: np.ndarray,
                          radius_km: np.ndarray, period_s: float) -> list:
    """Rank the disturbance sources and classify each as secular or cyclic.

    ``sources_mag[name]`` is the torque-magnitude time series; ``sources_mom``
    the cumulative momentum vector (N m s) for the same source.
    """
    t_s = np.asarray(t_s, dtype=float)
    radius_km = np.asarray(radius_km, dtype=float)
    peri = int(np.argmin(radius_km))
    apo = int(np.argmax(radius_km))

    entries = []
    for name, mag in sources_mag.items():
        mag = np.asarray(mag, dtype=float)
        H = np.asarray(sources_mom[name], dtype=float)
        secular_per_orbit, cyclic_swing = _secular_and_cyclic(t_s, H, period_s)
        secular_orbit = float(np.linalg.norm(secular_per_orbit))
        # Ratio of net-per-orbit (secular) to in-orbit excursion (cyclic).
        ratio = secular_orbit / (cyclic_swing + 1e-30)
        if ratio > 1.5:
            behaviour = "secular"
        elif ratio < 0.67:
            behaviour = "cyclic"
        else:
            behaviour = "mixed"
        entries.append({
            "source": name,
            "peak_nm": float(np.max(mag)),
            "perigee_nm": float(mag[peri]),
            "apogee_nm": float(mag[apo]),
            "secular_per_orbit_nms": secular_orbit,
            "cyclic_swing_nms": cyclic_swing,
            "behaviour": behaviour,
        })
    entries.sort(key=lambda e: e["peak_nm"], reverse=True)
    return entries
