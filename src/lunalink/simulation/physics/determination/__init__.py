"""Attitude determination: sensor models + complementary filter (framework Sec. 5)."""
from .sensors import (
    gyro_measurement, star_tracker_measurement,
    ARCSEC_TO_RAD, DEG_PER_HR_TO_RAD_S,
)
from .estimator import (
    propagate_estimate, star_update, knowledge_error_deg,
)

__all__ = [
    "gyro_measurement", "star_tracker_measurement",
    "ARCSEC_TO_RAD", "DEG_PER_HR_TO_RAD_S",
    "propagate_estimate", "star_update", "knowledge_error_deg",
]
