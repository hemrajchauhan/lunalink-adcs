"""Quaternion attitude kinematics and helpers (framework Sec. 4).

Convention: scalar-last unit quaternion q = [q1, q2, q3, q4] with q4 the scalar
part. R(q) is the body<-inertial rotation matrix (Eq. 12).
"""
import numpy as np


def normalize(q: np.ndarray) -> np.ndarray:
    n = np.linalg.norm(q)
    return q / n if n > 0 else np.array([0.0, 0.0, 0.0, 1.0])


def skew(a: np.ndarray) -> np.ndarray:
    return np.array([[0, -a[2], a[1]],
                     [a[2], 0, -a[0]],
                     [-a[1], a[0], 0]])


def quat_to_matrix(q: np.ndarray) -> np.ndarray:
    """Body<-inertial rotation matrix R(q) (framework Eq. 12)."""
    qv = q[:3]
    q4 = q[3]
    return ((q4 ** 2 - qv @ qv) * np.eye(3)
            + 2 * np.outer(qv, qv)
            - 2 * q4 * skew(qv))


def quat_multiply(a: np.ndarray, b: np.ndarray) -> np.ndarray:
    """Hamilton product a (X) b, scalar-last."""
    av, a4 = a[:3], a[3]
    bv, b4 = b[:3], b[3]
    v = a4 * bv + b4 * av + np.cross(av, bv)
    s = a4 * b4 - av @ bv
    return np.array([v[0], v[1], v[2], s])


def quat_conjugate(q: np.ndarray) -> np.ndarray:
    return np.array([-q[0], -q[1], -q[2], q[3]])


def quat_derivative(q: np.ndarray, omega: np.ndarray) -> np.ndarray:
    """q_dot = 1/2 Omega(omega) q (framework Eq. 13)."""
    w1, w2, w3 = omega
    omega_mat = np.array([
        [0, w3, -w2, w1],
        [-w3, 0, w1, w2],
        [w2, -w1, 0, w3],
        [-w1, -w2, -w3, 0],
    ])
    return 0.5 * omega_mat @ q


def quat_error(q_cmd: np.ndarray, q: np.ndarray) -> np.ndarray:
    """Error quaternion q_e = q_cmd^{-1} (X) q (framework Eq. 35)."""
    return normalize(quat_multiply(quat_conjugate(q_cmd), q))


def matrix_to_quat(R: np.ndarray) -> np.ndarray:
    """Body<-inertial rotation matrix -> scalar-last unit quaternion."""
    tr = np.trace(R)
    if tr > 0:
        s = np.sqrt(tr + 1.0) * 2
        q4 = 0.25 * s
        q1 = (R[2, 1] - R[1, 2]) / s
        q2 = (R[0, 2] - R[2, 0]) / s
        q3 = (R[1, 0] - R[0, 1]) / s
    elif R[0, 0] > R[1, 1] and R[0, 0] > R[2, 2]:
        s = np.sqrt(1.0 + R[0, 0] - R[1, 1] - R[2, 2]) * 2
        q4 = (R[2, 1] - R[1, 2]) / s
        q1 = 0.25 * s
        q2 = (R[0, 1] + R[1, 0]) / s
        q3 = (R[0, 2] + R[2, 0]) / s
    elif R[1, 1] > R[2, 2]:
        s = np.sqrt(1.0 + R[1, 1] - R[0, 0] - R[2, 2]) * 2
        q4 = (R[0, 2] - R[2, 0]) / s
        q1 = (R[0, 1] + R[1, 0]) / s
        q2 = 0.25 * s
        q3 = (R[1, 2] + R[2, 1]) / s
    else:
        s = np.sqrt(1.0 + R[2, 2] - R[0, 0] - R[1, 1]) * 2
        q4 = (R[1, 0] - R[0, 1]) / s
        q1 = (R[0, 2] + R[2, 0]) / s
        q2 = (R[1, 2] + R[2, 1]) / s
        q3 = 0.25 * s
    # Return the conjugate so this is the exact inverse of quat_to_matrix,
    # which uses the framework's body<-inertial convention (Eq. 12).
    return normalize(np.array([-q1, -q2, -q3, q4]))


def target_dcm_point_axis(target_inertial: np.ndarray,
                          reference: np.ndarray = np.array([0.0, 0.0, 1.0])
                          ) -> np.ndarray:
    """Body<-inertial DCM that puts ``target_inertial`` along body +z."""
    b3 = target_inertial / np.linalg.norm(target_inertial)
    a = reference
    if abs(np.dot(a, b3)) > 0.99:
        a = np.array([1.0, 0.0, 0.0])
    b1 = np.cross(a, b3)
    b1 /= np.linalg.norm(b1)
    b2 = np.cross(b3, b1)
    return np.vstack([b1, b2, b3])


def quat_to_euler321(q: np.ndarray) -> np.ndarray:
    """Yaw-pitch-roll (3-2-1) Euler angles in radians, for reporting plots."""
    R = quat_to_matrix(q)
    pitch = -np.arcsin(np.clip(R[0, 2], -1.0, 1.0))
    roll = np.arctan2(R[1, 2], R[2, 2])
    yaw = np.arctan2(R[0, 1], R[0, 0])
    return np.array([roll, pitch, yaw])


def pointing_error_deg(q: np.ndarray, target_inertial: np.ndarray,
                       body_axis: np.ndarray = np.array([0.0, 0.0, 1.0])) -> float:
    """Angle between the chosen body axis and a target direction (Eq. 15)."""
    target_body = quat_to_matrix(q) @ (target_inertial / np.linalg.norm(target_inertial))
    cos_a = np.clip(np.dot(body_axis, target_body), -1.0, 1.0)
    return np.degrees(np.arccos(cos_a))
