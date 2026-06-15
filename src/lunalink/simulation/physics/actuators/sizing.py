"""Actuator sizing hand-calcs (framework Sec. 8, Eq. 29-31).

Reaction-wheel sizing has two drivers:
  - Slew (rest-to-rest):  T_slew = 4 I theta / t^2,  h_slew = T_slew t / 2  (Eq. 29)
  - Cyclic storage:       h_store = T_D P / 4 * 0.707                       (Eq. 30)
Magnetorquer dipole:      |m| = (margin) T_C / B                           (Eq. 31)
"""
import numpy as np

from ..constants import GM_EARTH
from ..orbit.kepler import orbital_period_s
from ..dynamics.mass_properties import box_inertia


def slew_sizing(inertia_max: float, slew_angle_rad: float, slew_time_s: float):
    """Rest-to-rest slew torque and peak wheel momentum (Eq. 29)."""
    T_slew = 4 * inertia_max * slew_angle_rad / slew_time_s ** 2
    return T_slew, T_slew * slew_time_s / 2


def cyclic_storage(peak_disturbance_nm: float, period_s: float) -> float:
    """RMS momentum stored over a quarter orbit (Eq. 30)."""
    return peak_disturbance_nm * period_s / 4 * 0.707


def magnetorquer_dipole(control_torque_nm: float, field_t: float,
                        margin: float = 1.0) -> float:
    """Required dipole |m| = margin * T_C / B (Eq. 31)."""
    return margin * control_torque_nm / field_t if field_t > 0 else float("inf")


def sizing_summary(mass_kg: float, dims_m, semi_major_axis_m: float,
                   apogee_disturbance_nm: float = 3.3e-6,
                   slew_angle_deg: float = 90.0, slew_time_s: float = 300.0) -> dict:
    """Convenience summary used by the GUI/report for a given spacecraft."""
    I = box_inertia(mass_kg, dims_m)
    period_s = orbital_period_s(semi_major_axis_m, GM_EARTH)
    T_slew, h_slew = slew_sizing(I.max(), np.radians(slew_angle_deg), slew_time_s)
    h_store = cyclic_storage(apogee_disturbance_nm, period_s)
    return {
        "inertia_kgm2": I,
        "slew_torque_nm": T_slew,
        "slew_momentum_nms": h_slew,
        "cyclic_storage_nms": h_store,
        "recommended_wheel_hmax_nms": max(h_slew, h_store) * 1.5,
    }
