from dataclasses import dataclass
import numpy as np

@dataclass
class SpaceObject:
    name: str
    position_m: np.ndarray
    color: str

@dataclass
class CelestialBody(SpaceObject):
    radius_m: float

@dataclass
class Satellite(SpaceObject):
    mass_kg: float
    dimensions_m: tuple[float, float, float] # (length, width, height) for each component]