"""Attitude sensor models (framework Sec. 5, the determination half of ADCS).

We model the two sensors that bound the pointing-knowledge budget:

* **Rate gyro** - measures body angular velocity but is corrupted by a slowly
  varying **bias** and white **noise**:  ``w_meas = w_true + bias + noise``.
  Integrating it open-loop therefore *drifts*.
* **Star tracker** - measures the absolute attitude quaternion to high accuracy
  but at a slower rate; modelled as truth perturbed by a small random rotation.

The complementary filter in ``estimator.py`` fuses the two: it integrates the
fast gyro for a smooth high-rate estimate and uses the occasional star fix to
reset the drift and learn the gyro bias.
"""
import numpy as np

from ..attitude import quat_multiply, normalize, quat_from_axis_angle

ARCSEC_TO_RAD = np.pi / (180.0 * 3600.0)
DEG_PER_HR_TO_RAD_S = (np.pi / 180.0) / 3600.0


def gyro_measurement(omega_true: np.ndarray, bias: np.ndarray,
                     noise_std_rad_s: float, rng: np.random.Generator) -> np.ndarray:
    """Biased, noisy body-rate measurement ``w_true + bias + noise`` (rad/s)."""
    return omega_true + bias + rng.normal(0.0, noise_std_rad_s, 3)


def star_tracker_measurement(q_true: np.ndarray, noise_std_rad: float,
                             rng: np.random.Generator) -> np.ndarray:
    """Absolute attitude fix: truth perturbed by a small random rotation."""
    dtheta = rng.normal(0.0, noise_std_rad, 3)
    angle = np.linalg.norm(dtheta)
    if angle < 1e-15:
        return normalize(np.asarray(q_true, dtype=float))
    dq = quat_from_axis_angle(dtheta / angle, angle)
    return normalize(quat_multiply(q_true, dq))
