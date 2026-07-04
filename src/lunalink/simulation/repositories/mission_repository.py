"""Persistence for missions (``missions.json``).

A mission ties a satellite to a set of simulation-parameter overrides that are
merged on top of the JSON simulation defaults at run time.
"""
from ..objects import Mission
from ..defaults import load_simulation_defaults
from .json_store import JsonRepository


class MissionRepository(JsonRepository):

    FILENAME = "missions.json"

    # -- record (de)serialisation -----------------------------------------
    def decode(self, record: dict) -> Mission:
        return Mission.from_dict(record)

    def encode(self, mission: Mission) -> dict:
        return mission.to_dict()

    # -- named operations ------------------------------------------------
    def add_mission(self, mission: Mission) -> None:
        self.upsert(mission)                 # replaces an existing same-name mission

    def delete_mission(self, name: str) -> None:
        self.delete(name)

    # -- parameter resolution ------------------------------------------------
    def resolved_simulation_params(self, name: str) -> dict:
        """Simulation defaults merged with this mission's overrides."""
        mission = self.get_by_name(name)
        params = load_simulation_defaults()
        if mission is not None:
            params.update(mission.simulation)
        return params
