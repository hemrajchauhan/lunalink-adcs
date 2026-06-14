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