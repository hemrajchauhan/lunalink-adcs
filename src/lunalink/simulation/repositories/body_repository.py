from pathlib import Path
import json

from ..objects import CelestialBody, OrbitElements


class BodyRepository:

    def __init__(self):
        self.path = Path(__file__).parents[2] / "data" / "bodies.json"

    # -- (de)serialization -------------------------------------------------
    def _to_body(self, item: dict) -> CelestialBody:
        return CelestialBody(
            name=item["name"],
            color=item["color"],
            radius_m=float(item["radius_m"]),
            axial_tilt_deg=float(item.get("axial_tilt_deg", 0.0)),
            rotation_period_h=float(item.get("rotation_period_h", 24.0)),
            has_ring=bool(item.get("has_ring", False)),
            parent=item.get("parent"),
            orbit=OrbitElements.from_dict(item.get("orbit")),
        )

    def _to_dict(self, body: CelestialBody) -> dict:
        return {
            "name": body.name,
            "color": body.color,
            "radius_m": body.radius_m,
            "axial_tilt_deg": body.axial_tilt_deg,
            "rotation_period_h": body.rotation_period_h,
            "has_ring": body.has_ring,
            "parent": body.parent,
            "orbit": body.orbit.to_dict() if body.orbit else None,
        }

    # -- persistence -------------------------------------------------------
    def load_all(self) -> list[CelestialBody]:
        with open(self.path, "r", encoding="utf-8") as file:
            data = json.load(file)
        return [self._to_body(item) for item in data]

    def save_all(self, bodies: list[CelestialBody]) -> None:
        data = [self._to_dict(body) for body in bodies]
        with open(self.path, "w", encoding="utf-8") as file:
            json.dump(data, file, indent=4)

    def add_body(self, body: CelestialBody) -> None:
        bodies = self.load_all()
        bodies.append(body)
        self.save_all(bodies)

    def update_body(self, updated_body: CelestialBody) -> None:
        bodies = self.load_all()
        for index, body in enumerate(bodies):
            if body.name == updated_body.name:
                bodies[index] = updated_body
                break
        self.save_all(bodies)

    def delete_body(self, body_name: str) -> None:
        bodies = [b for b in self.load_all() if b.name != body_name]
        self.save_all(bodies)

    def get_by_name(self, name: str) -> CelestialBody | None:
        return next((b for b in self.load_all() if b.name == name), None)

    # -- property editor support ------------------------------------------
    def get_properties(self, body_name: str):
        body = self.get_by_name(body_name)
        if body is None:
            return []
        orbit = body.orbit or OrbitElements(semi_major_axis_m=0.0)
        return [
            ("Name", body.name),
            ("Color", body.color),
            ("Radius (m)", body.radius_m),
            ("Axial tilt (deg)", body.axial_tilt_deg),
            ("Rotation period (h)", body.rotation_period_h),
            ("Has ring", body.has_ring),
            ("Parent", body.parent or ""),
            ("Distance to parent (m)", orbit.semi_major_axis_m),
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
                semi_major_axis_m=float(properties["Distance to parent (m)"]),
                eccentricity=float(properties["Eccentricity"]),
                inclination_deg=float(properties["Inclination (deg)"]),
                raan_deg=float(properties["RAAN (deg)"]),
                arg_periapsis_deg=float(properties["Arg periapsis (deg)"]),
                mean_anomaly_epoch_deg=float(properties["Mean anomaly (deg)"]),
            )

        body = CelestialBody(
            name=properties["Name"],
            color=properties["Color"],
            radius_m=float(properties["Radius (m)"]),
            axial_tilt_deg=float(properties["Axial tilt (deg)"]),
            rotation_period_h=float(properties["Rotation period (h)"]),
            has_ring=str(properties.get("Has ring", "False")).lower() in ("true", "1", "yes"),
            parent=parent,
            orbit=orbit,
        )

        bodies = self.load_all()
        for index, existing in enumerate(bodies):
            if existing.name == original_name:
                bodies[index] = body
                break
        else:
            bodies.append(body)
        self.save_all(bodies)
