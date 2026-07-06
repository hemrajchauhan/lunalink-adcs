"""Persistence for celestial bodies (``bodies.json``)."""
from ..objects import CelestialBody, OrbitElements
from .json_store import JsonRepository

_TRUTHY = ("true", "1", "yes")


class BodyRepository(JsonRepository):

    FILENAME = "bodies.json"

    # -- record (de)serialisation -----------------------------------------
    def decode(self, record: dict) -> CelestialBody:
        return CelestialBody(
            name=record["name"],
            color=record["color"],
            radius_m=float(record["radius_m"]),
            axial_tilt_deg=float(record.get("axial_tilt_deg", 0.0)),
            rotation_period_h=float(record.get("rotation_period_h", 24.0)),
            has_ring=bool(record.get("has_ring", False)),
            parent=record.get("parent"),
            orbit=OrbitElements.from_dict(record.get("orbit")),
        )

    def encode(self, body: CelestialBody) -> dict:
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

    # -- named operations (kept for call-site readability) ------------------
    def add_body(self, body: CelestialBody) -> None:
        self.add(body)

    def delete_body(self, name: str) -> None:
        self.delete(name)

    # -- property editor support --------------------------------------------
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
            has_ring=str(properties.get("Has ring", "False")).lower() in _TRUTHY,
            parent=parent,
            orbit=orbit,
        )
        self.upsert(body, original_name)
