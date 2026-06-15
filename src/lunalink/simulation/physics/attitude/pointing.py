"""Pointing geometry: error quaternion, Euler angles and pointing error
(framework Sec. 4.2-4.3, Eq. 14-15).
"""
import numpy as np

from .quaternion import quat_to_matrix, quat_multiply, quat_conjugate, normalize


def quat_error(q_cmd: np.ndarray, q: np.ndarray) -> np.ndarray:
    """Error quaternion q_e = q_cmd^{-1} (x) q (framework Eq. 35)."""
    return normalize(quat_multiply(quat_conjugate(q_cmd), q))


def quat_to_euler321(q: np.ndarray) -> np.ndarray:
    """Yaw-pitch-roll (3-2-1) Euler angles (rad) for reporting (Eq. 14)."""
    R = quat_to_matrix(q)
    pitch = -np.arcsin(np.clip(R[0, 2], -1.0, 1.0))
    roll = np.arctan2(R[1, 2], R[2, 2])
    yaw = np.arctan2(R[0, 1], R[0, 0])
    return np.array([roll, pitch, yaw])


def pointing_error_deg(q: np.ndarray, target_inertial: np.ndarray,
                       body_axis: np.ndarray = np.array([0.0, 0.0, 1.0])) -> float:
    """Angle between a body axis and a target direction (framework Eq. 15)."""
    target_body = quat_to_matrix(q) @ (target_inertial / np.linalg.norm(target_inertial))
    return np.degrees(np.arccos(np.clip(np.dot(body_axis, target_body), -1.0, 1.0)))


def target_dcm_point_axis(target_inertial: np.ndarray,
                          reference: np.ndarray = np.array([0.0, 0.0, 1.0])) -> np.ndarray:
    """Body<-inertial DCM that aligns body +z with ``target_inertial``."""
    b3 = target_inertial / np.linalg.norm(target_inertial)
    a = reference
    if abs(np.dot(a, b3)) > 0.99:
        a = np.array([1.0, 0.0, 0.0])
    b1 = np.cross(a, b3)
    b1 /= np.linalg.norm(b1)
    b2 = np.cross(b3, b1)
    return np.vstack([b1, b2, b3])
