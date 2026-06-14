import numpy as np

from ...config import DISTANCE_SCALE, BODY_SCALE, SATELLITE_SCALE

class VisualizationTransform:
    
    @staticmethod
    def position(position_m: np.ndarray) -> np.ndarray:
        return position_m * DISTANCE_SCALE

    @staticmethod
    def radius(radius_m: float) -> float:
        return radius_m * BODY_SCALE

    @staticmethod
    def satellite_dimensions(dimensions_m: tuple[float, float, float]) -> tuple[float, float, float]:
        return tuple(dim * SATELLITE_SCALE for dim in dimensions_m)