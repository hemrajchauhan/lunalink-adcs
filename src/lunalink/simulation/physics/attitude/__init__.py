"""Attitude representation and kinematics (framework Sec. 4)."""
from .quaternion import (
    normalize, skew, quat_to_matrix, quat_multiply, quat_conjugate,
    quat_derivative, matrix_to_quat,
)
from .pointing import (
    quat_error, quat_to_euler321, pointing_error_deg, target_dcm_point_axis,
)

__all__ = [
    "normalize", "skew", "quat_to_matrix", "quat_multiply", "quat_conjugate",
    "quat_derivative", "matrix_to_quat", "quat_error", "quat_to_euler321",
    "pointing_error_deg", "target_dcm_point_axis",
]
