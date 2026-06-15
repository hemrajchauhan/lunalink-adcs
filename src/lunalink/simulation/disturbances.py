"""Environmental disturbance torques in body axes (framework Sec. 6, Eq. 19-22).

Each function returns a torque vector (N m) in the body frame. ``R_bi`` is the
body<-inertial rotation matrix R(q).
"""
import numpy as np

from ..config import GM_EARTH

SOLAR_CONST = 1361.0          # Phi, W/m^2
LIGHT_SPEED = 3.0e8           # c, m/s


def gravity_gradient(R_bi: np.ndarray, r_eci: np.ndarray,
                     inertia: np.ndarray) -> np.ndarray:
    """Gravity-gradient torque (framework Eq. 19, vector form)."""
    R = np.linalg.norm(r_eci)
    if R == 0:
        return np.zeros(3)
    n_body = R_bi @ (r_eci / R)              # nadir direction in body axes
    I_n = inertia * n_body                   # diagonal inertia
    return 3.0 * GM_EARTH / R ** 3 * np.cross(n_body, I_n)


def solar_radiation(R_bi: np.ndarray, sun_hat_eci: np.ndarray, in_eclipse: bool,
                    area_m2: float, reflectance: float, cp_offset_body: np.ndarray
                    ) -> np.ndarray:
    """Solar-radiation-pressure torque (framework Eq. 20). Zero in eclipse."""
    if in_eclipse:
        return np.zeros(3)
    sun_body = R_bi @ sun_hat_eci
    # Force on the effective sun-facing area, directed away from the Sun.
    # (area_m2 is the projected illuminated area, always lit while in sunlight.)
    force = -(SOLAR_CONST / LIGHT_SPEED) * area_m2 * (1 + reflectance) * sun_body
    return np.cross(cp_offset_body, force)


def magnetic(residual_dipole_body: np.ndarray, B_body: np.ndarray) -> np.ndarray:
    """Residual-dipole magnetic torque T = D x B (framework Eq. 21)."""
    return np.cross(residual_dipole_body, B_body)


def aerodynamic(R_bi: np.ndarray, v_eci: np.ndarray, density: float,
                drag_coeff: float, area_m2: float, cp_offset_body: np.ndarray
                ) -> np.ndarray:
    """Aerodynamic drag torque (framework Eq. 22). Negligible above ~600 km."""
    v = np.linalg.norm(v_eci)
    if v == 0 or density <= 0:
        return np.zeros(3)
    v_body = R_bi @ (v_eci / v)
    force = -0.5 * density * drag_coeff * area_m2 * v ** 2 * v_body
    return np.cross(cp_offset_body, force)
