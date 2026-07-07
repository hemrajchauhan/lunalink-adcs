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
            mass_kg=float(record.get("mass_kg", 0.0)),
            magnetic_dipole_tm3=float(record.get("magnetic_dipole_tm3", 0.0)),
            atmosphere_ref_density_kg_m3=float(
                record.get("atmosphere_ref_density_kg_m3", 0.0)),
            atmosphere_ref_altitude_m=float(
                record.get("atmosphere_ref_altitude_m", 0.0)),
            atmosphere_scale_height_m=float(
                record.get("atmosphere_scale_height_m", 60_000.0)),
            j2=float(record.get("j2", 0.0)),
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
            "mass_kg": body.mass_kg,
            "magnetic_dipole_tm3": body.magnetic_dipole_tm3,
            "atmosphere_ref_density_kg_m3": body.atmosphere_ref_density_kg_m3,
            "atmosphere_ref_altitude_m": body.atmosphere_ref_altitude_m,
            "atmosphere_scale_height_m": body.atmosphere_scale_height_m,
            "j2": body.j2,
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
            ("Mass (kg)", body.mass_kg),
            ("Magnetic dipole (T m^3)", body.magnetic_dipole_tm3),
            ("Atmosphere density (kg/m^3)", body.atmosphere_ref_density_kg_m3),
            ("Atmosphere ref altitude (m)", body.atmosphere_ref_altitude_m),
            ("Atmosphere scale height (m)", body.atmosphere_scale_height_m),
            ("J2 oblateness", body.j2),
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
        def _num(key, default=0.0):
            try:
                return float(properties.get(key, default))
            except (TypeError, ValueError):
                return float(default)

        body = CelestialBody(
            name=properties["Name"],
            color=properties["Color"],
            radius_m=float(properties["Radius (m)"]),
            axial_tilt_deg=float(properties["Axial tilt (deg)"]),
            rotation_period_h=float(properties["Rotation period (h)"]),
            has_ring=str(properties.get("Has ring", "False")).lower() in _TRUTHY,
            parent=parent,
            orbit=orbit,
            mass_kg=_num("Mass (kg)"),
            magnetic_dipole_tm3=_num("Magnetic dipole (T m^3)"),
            atmosphere_ref_density_kg_m3=_num("Atmosphere density (kg/m^3)"),
            atmosphere_ref_altitude_m=_num("Atmosphere ref altitude (m)"),
            atmosphere_scale_height_m=_num("Atmosphere scale height (m)", 60_000.0),
            j2=_num("J2 oblateness"),
        )
        self.upsert(body, original_name)
