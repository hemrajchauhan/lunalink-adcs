"""Solar-system model: owns every body/satellite and resolves their absolute
positions at a given simulation time.

The Sun sits at the origin and is assumed stationary. Every other object is
positioned relative to its parent via Keplerian propagation, resolved
hierarchically (Sun -> planet -> moon/satellite).
"""
import numpy as np

from .physics import orbit
from .physics.constants import GM_SUN, GM_EARTH, GM_BODIES
from .objects import SpaceObject
from .repositories.body_repository import BodyRepository
from .repositories.satellite_repository import SatelliteRepository


class SolarSystem:

    def __init__(self):
        self.bodies = []
        self.satellites = []
        self.reload()

    def reload(self):
        self.bodies = BodyRepository().load_all()
        self.satellites = SatelliteRepository().load_all()

    # -- lookups ----------------------------------------------------------
    def all_objects(self) -> list[SpaceObject]:
        return [*self.bodies, *self.satellites]

    def get_object(self, name: str) -> SpaceObject | None:
        return next((o for o in self.all_objects() if o.name == name), None)

    def body_names(self) -> list[str]:
        return [b.name for b in self.bodies]

    def mu_for(self, parent_name: str | None) -> float:
        if parent_name is None:
            return GM_SUN
        return GM_BODIES.get(parent_name, GM_EARTH)

    # -- propagation ------------------------------------------------------
    def compute_positions(self, time_s: float) -> dict[str, np.ndarray]:
        """Resolve absolute positions for all objects, caching onto each
        object's ``position_m`` and returning a name -> position dict."""
        positions: dict[str, np.ndarray] = {}
        for obj in self.all_objects():
            pos = self._resolve(obj, time_s, positions)
            obj.position_m = pos
            positions[obj.name] = pos
        return positions

    def _resolve(self, obj: SpaceObject, time_s: float,
                 positions: dict[str, np.ndarray]) -> np.ndarray:
        # Root body (the Sun): origin.
        if obj.parent is None or obj.orbit is None:
            return np.zeros(3)

        # Make sure the parent is resolved first.
        if obj.parent in positions:
            parent_pos = positions[obj.parent]
        else:
            parent_obj = self.get_object(obj.parent)
            parent_pos = (self._resolve(parent_obj, time_s, positions)
                          if parent_obj is not None else np.zeros(3))
            positions[obj.parent] = parent_pos

        local = orbit.position_in_parent_frame(
            obj.orbit, self.mu_for(obj.parent), time_s)
        return parent_pos + local

    def orbit_path_world(self, obj: SpaceObject,
                         positions: dict[str, np.ndarray],
                         samples: int = 200) -> np.ndarray | None:
        """Orbit trace in world coordinates (parent's current position + the
        local ellipse). Returns None for objects without an orbit."""
        if obj.orbit is None or obj.parent is None:
            return None
        parent_pos = positions.get(obj.parent, np.zeros(3))
        local_path = orbit.orbit_path_points(obj.orbit, samples)
        return local_path + parent_pos
