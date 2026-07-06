"""Persistence for spacecraft (``satellites.json``)."""
import numpy as np

from ..objects import Satellite, OrbitElements
from .json_store import JsonRepository


class SatelliteRepository(JsonRepository):

    FILENAME = "satellites.json"

    # -- record (de)serialisation -----------------------------------------
    def decode(self, record: dict) -> Satellite:
        return Satellite(
            name=record["name"],
            color=record["color"],
            mass_kg=float(record["mass_kg"]),
            dimensions_m=np.array(record["dimensions_m"], dtype=float),
            parent=record.get("parent"),
            orbit=OrbitElements.from_dict(record.get("orbit")),
        )

    def encode(self, satellite: Satellite) -> dict:
        return {
            "name": satellite.name,
            "color": satellite.color,
            "mass_kg": satellite.mass_kg,
            "dimensions_m": np.asarray(satellite.dimensions_m).tolist(),
            "parent": satellite.parent,
            "orbit": satellite.orbit.to_dict() if satellite.orbit else None,
        }

    # -- named operations (kept for call-site readability) ------------------
    def add_satellite(self, satellite: Satellite) -> None:
        self.add(satellite)

    def delete_satellite(self, name: str) -> None:
        self.delete(name)

    # -- property editor support --------------------------------------------
    def get_properties(self, satellite_name: str):
        satellite = self.get_by_name(satellite_name)
        if satellite is None:
            return []
        orbit = satellite.orbit or OrbitElements(semi_major_axis_m=0.0)
        dims = np.asarray(satellite.dimensions_m)
        return [
            ("Name", satellite.name),
            ("Color", satellite.color),
            ("Mass (kg)", satellite.mass_kg),
            ("Length (m)", dims[0]),
            ("Width (m)", dims[1]),
            ("Height (m)", dims[2]),
            ("Parent", satellite.parent or ""),
            ("Semi-major axis (m)", orbit.semi_major_axis_m),
            ("Eccentricity", orbit.eccentricity),
            ("Inclination (deg)", orbit.inclination_deg),
            ("RAAN (deg)", orbit.raan_deg),
            ("Arg periapsis (deg)", orbit.arg_periapsis_deg),
            ("Mean anomaly (deg)", orbit.mean_anomaly_epoch_deg),
        ]

    def save_properties(self, original_name: str, properties: dict) -> None:
        parent = (properties.get("Parent") or "").strip() or None
        orbit = None
        if parent is not None:
            orbit = OrbitElements(
                semi_major_axis_m=float(properties["Semi-major axis (m)"]),
                eccentricity=float(properties["Eccentricity"]),
                inclination_deg=float(properties["Inclination (deg)"]),
                raan_deg=float(properties["RAAN (deg)"]),
                arg_periapsis_deg=float(properties["Arg periapsis (deg)"]),
                mean_anomaly_epoch_deg=float(properties["Mean anomaly (deg)"]),
            )
        satellite = Satellite(
            name=properties["Name"],
            color=properties["Color"],
            mass_kg=float(properties["Mass (kg)"]),
            dimensions_m=np.array([
                float(properties["Length (m)"]),
                float(properties["Width (m)"]),
                float(properties["Height (m)"]),
            ]),
            parent=parent,
            orbit=orbit,
        )
        self.upsert(satellite, original_name)
