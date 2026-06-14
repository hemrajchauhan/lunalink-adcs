from pathlib import Path
import json
import numpy as np

from ..objects import Satellite

class SatelliteRepository:

    def __init__(self):
        self.path = Path(__file__).parents[2] / "data" / "satellites.json"

    def load_all(self):
        with open(self.path, "r") as file:
            data = json.load(file)

        satellites = []

        for item in data:
            satellites.append(Satellite(
                name=item["name"],
                mass_kg=item["mass_kg"],
                dimensions_m=np.array(item["dimensions_m"]),
                position_m=np.array(item["position_m"]),
                color=item["color"],
                )
            )

        return satellites

    def save_all (self, satellites: list[Satellite]) -> None:
        data = []
        for satellite in satellites:
            data.append({
                "name": satellite.name,
                "mass_kg": satellite.mass_kg,
                "dimensions_m": satellite.dimensions_m.tolist(),
                "position_m": satellite.position_m.tolist(),
                "color": satellite.color
            })
        with open(self.path, "w") as file:
            json.dump(data, file, indent=4)

    def update_satellite(self, updated_satellite):
        satellites = self.load_all()
        for index, satellite in enumerate(satellites):
            if satellite.name == updated_satellite.name:
                satellites[index] = updated_satellite
                break
        self.save_all(satellites)

    def add_satellite(self, satellite: Satellite) -> None:
        satellites = self.load_all()
        satellites.append(satellite)
        self.save_all(satellites)

    def delete_satellite(self, satellite_name: str) -> None:
        satellites = self.load_all()
        satellites = [satellite for satellite in satellites if satellite.name != satellite_name]
        self.save_all(satellites)

    def get_by_name(self, name: str) -> Satellite | None:
        satellites = self.load_all()
        for satellite in satellites:
            if satellite.name == name:
                return satellite
        return None

    def get_properties(self, satellite_name: str):
        satellite = self.get_by_name(satellite_name)
        if satellite is None:
            return []
        return [
            ("Name", satellite.name),
            ("Mass (kg)", satellite.mass_kg),
            ("Color", satellite.color),
            ("Position X (m)", satellite.position_m[0]),
            ("Position Y (m)", satellite.position_m[1]),
            ("Position Z (m)", satellite.position_m[2]),
            ("Length (m)", satellite.dimensions_m[0]),
            ("Width (m)", satellite.dimensions_m[1]),
            ("Height (m)", satellite.dimensions_m[2]),
        ]

    def save_properties(self, original_name: str, properties: dict):
        satellite = Satellite(
            name=properties["Name"],
            mass_kg=float(properties["Mass (kg)"]),
            dimensions_m=np.array([
                float(properties["Length (m)"]), 
                float(properties["Width (m)"]), 
                float(properties["Height (m)"])
            ]),
            position_m=np.array([
                float(properties["Position X (m)"]),
                float(properties["Position Y (m)"]),
                float(properties["Position Z (m)"])
            ]),
            color=properties["Color"]
        )

        satellites = self.load_all()

        for index, existing_satellite in enumerate(satellites):
            if existing_satellite.name == original_name:
                satellites[index] = satellite
                break

        self.save_all(satellites)