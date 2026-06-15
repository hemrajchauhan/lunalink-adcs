from pathlib import Path
import json

from ..objects import Mission
from ..defaults import load_simulation_defaults


class MissionRepository:
    """Reads/writes the missions defined in missions.json. A mission ties a
    satellite to a set of simulation parameter overrides on top of the
    JSON simulation defaults."""

    def __init__(self):
        self.path = Path(__file__).parents[2] / "data" / "missions.json"

    def load_all(self) -> list[Mission]:
        try:
            with open(self.path, "r", encoding="utf-8") as file:
                data = json.load(file)
        except (OSError, ValueError):
            return []
        return [Mission.from_dict(item) for item in data]

    def save_all(self, missions: list[Mission]) -> None:
        data = [m.to_dict() for m in missions]
        with open(self.path, "w", encoding="utf-8") as file:
            json.dump(data, file, indent=4)

    def get_by_name(self, name: str) -> Mission | None:
        return next((m for m in self.load_all() if m.name == name), None)

    def add_mission(self, mission: Mission) -> None:
        missions = [m for m in self.load_all() if m.name != mission.name]
        missions.append(mission)
        self.save_all(missions)

    def delete_mission(self, name: str) -> None:
        self.save_all([m for m in self.load_all() if m.name != name])

    def resolved_simulation_params(self, name: str) -> dict:
        """Simulation defaults merged with this mission's overrides."""
        mission = self.get_by_name(name)
        params = load_simulation_defaults()
        if mission is not None:
            params.update(mission.simulation)
        return params
