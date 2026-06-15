"""Backward-compatibility shim - see :mod:`lunalink.simulation.physics.attitude`."""
from .physics.attitude import (  # noqa: F401
    normalize, skew, quat_to_matrix, quat_multiply, quat_conjugate,
    quat_derivative, matrix_to_quat, quat_error, quat_to_euler321,
    pointing_error_deg, target_dcm_point_axis,
)
