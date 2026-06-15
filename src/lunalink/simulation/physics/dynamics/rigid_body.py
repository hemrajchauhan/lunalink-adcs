"""Rigid-body rotational dynamics (framework Sec. 5.2, Eq. 17-18).

Wheel-augmented Euler equation, solved for the body angular acceleration:

    I omega_dot = -omega x (I omega + h_w) - h_w_dot + T_body

The kinematics q_dot come from attitude.quaternion. The state derivative below
is what the RK4 integrator advances.
"""
import numpy as np

from ..attitude.quaternion import quat_derivative


def state_derivative(q: np.ndarray, omega: np.ndarray, inertia: np.ndarray,
                     wheel_momentum: np.ndarray, wheel_torque: np.ndarray,
                     torque_body: np.ndarray):
    """Return (q_dot, omega_dot) for fixed control/disturbance over the step."""
    H_internal = inertia * omega + wheel_momentum
    omega_dot = (torque_body - wheel_torque - np.cross(omega, H_internal)) / inertia
    return quat_derivative(q, omega), omega_dot
