from pathlib import Path
import json
import numpy as np

from ..objects import Satellite, OrbitElements


class SatelliteRepository:

    def __init__(self):
        self.path = Path(__file__).parents[2] / "data" / "satellites.json"

    # -- (de)serialization -------------------------------------------------
    def _to_satellite(self, item: dict) -> Satellite:
        return Satellite(
            name=item["name"],
            color=item["color"],
            mass_kg=float(item["mass_kg"]),
            dimensions_m=np.array(item["dimensions_m"], dtype=float),
            parent=item.get("parent"),
            orbit=OrbitElements.from_dict(item.get("orbit")),
        )

    def _to_dict(self, satellite: Satellite) -> dict:
        return {
            "name": satellite.name,
            "color": satellite.color,
            "mass_kg": satellite.mass_kg,
            "dimensions_m": np.asarray(satellite.dimensions_m).tolist(),
            "parent": satellite.parent,
            "orbit": satellite.orbit.to_dict() if satellite.orbit else None,
        }

    # -- persistence -------------------------------------------------------
    def load_all(self) -> list[Satellite]:
        with open(self.path, "r", encoding="utf-8") as file:
            data = json.load(file)
        return [self._to_satellite(item) for item in data]

    def save_all(self, satellites: list[Satellite]) -> None:
        data = [self._to_dict(satellite) for satellite in satellites]
        with open(self.path, "w", encoding="utf-8") as file:
            json.dump(data, file, indent=4)

    def add_satellite(self, satellite: Satellite) -> None:
        satellites = self.load_all()
        satellites.append(satellite)
        self.save_all(satellites)

    def update_satellite(self, updated_satellite: Satellite) -> None:
        satellites = self.load_all()
        for index, satellite in enumerate(satellites):
            if satellite.name == updated_satellite.name:
                satellites[index] = updated_satellite
                break
        self.save_all(satellites)

    def delete_satellite(self, satellite_name: str) -> None:
        satellites = [s for s in self.load_all() if s.name != satellite_name]
        self.save_all(satellites)

    def get_by_name(self, name: str) -> Satellite | None:
        return next((s for s in self.load_all() if s.name == name), None)

    # -- property editor support ------------------------------------------
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

        satellites = self.load_all()
        for index, existing in enumerate(satellites):
            if existing.name == original_name:
                satellites[index] = satellite
                break
        else:
            satellites.append(satellite)
        self.save_all(satellites)
