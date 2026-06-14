from pathlib import Path
import json
import numpy as np

from ..objects import CelestialBody

class BodyRepository:

    def __init__(self):
        self.path = Path(__file__).parents[2] / "data" / "bodies.json"

    def load_all(self):
        with open(self.path, "r") as file:
            data = json.load(file)

        bodies = []

        for item in data:
            bodies.append(CelestialBody(
                name=item["name"],
                radius_m=item["radius_m"],
                position_m=np.array(item["position_m"]),
                color=item["color"],
                )
            )
        return bodies

    def save_all (self, bodies: list[CelestialBody]) -> None:
        
        data = []
        
        for body in bodies:
            data.append({
                "name": body.name,
                "radius_m": body.radius_m,
                "position_m": body.position_m.tolist(),
                "color": body.color
            })

        with open(self.path, "w") as file:
            json.dump(data, file, indent=4)

    def update_body(self, updated_body):
        bodies = self.load_all()
        for index, body in enumerate(bodies):
            if body.name == updated_body.name:
                bodies[index] = updated_body
                break
        self.save_all(bodies)

    def add_body(self, body: CelestialBody) -> None:
        bodies = self.load_all()
        bodies.append(body)
        self.save_all(bodies)

    def delete_body(self, body_name: str) -> None:
        bodies = self.load_all()
        bodies = [body for body in bodies if body.name != body_name]
        self.save_all(bodies)

    def get_by_name(self, name: str) -> CelestialBody | None:
        bodies = self.load_all()
        for body in bodies:
            if body.name == name:
                return body
        return None

    def get_properties(self, body_name: str):
        body = self.get_by_name(body_name)

        if body is None:
            return []
        return [
            ("Name", body.name),
            ("Radius (m)", body.radius_m),
            ("Color", body.color),
            ("Position X (m)", body.position_m[0]),
            ("Position Y (m)", body.position_m[1]),
            ("Position Z (m)", body.position_m[2]),
        ]
        
    def save_properties(self, original_name: str, properties: dict):
        body = CelestialBody(
            name=properties["Name"],
            radius_m=float(properties["Radius (m)"]),
            position_m=np.array([
                float(properties["Position X (m)"]),
                float(properties["Position Y (m)"]),
                float(properties["Position Z (m)"])
            ]),
            color=properties["Color"],
        )
        bodies = self.load_all()

        for index, existing_body in enumerate(bodies):
            if existing_body.name == original_name:
                bodies[index] = body
                break

        self.save_all(bodies)