"""Loaders for the JSON parameter files (so mission, orbit, spacecraft and
simulation parameters are data, not hard-coded).

    simulation_defaults.json - default ADCS simulation parameters
    mission_profile.json     - the fixed mission constants from the brief
"""
from pathlib import Path
import json

_DATA = Path(__file__).parents[1] / "data"

# Safety fallbacks if a JSON file is missing or unreadable.
_SIMULATION_FALLBACK = {
    "mode": "sun_pointing", "initial_tumble_deg_s": 10.0,
    "rw_max_momentum_nms": 4.0, "rw_max_torque_nm": 0.05,
    "magnetorquer_max_dipole_am2": 50.0, "residual_dipole_am2": 1.0,
    "srp_area_m2": 3.0, "reflectance": 0.5, "drag_coeff": 2.2,
    "cp_offset_m": 0.1, "natural_freq": 0.05, "damping": 0.7,
    "desat_gain": 1.0, "detumble_exit_deg_s": 1.0, "n_orbits": 3.0, "dt_s": 8.0,
}


def _load_json(name: str, fallback):
    try:
        with open(_DATA / name, "r", encoding="utf-8") as file:
            return json.load(file)
    except (OSError, ValueError):
        return fallback


def load_simulation_defaults() -> dict:
    data = _load_json("simulation_defaults.json", {})
    return {**_SIMULATION_FALLBACK, **data}


def load_mission_profile() -> dict:
    return _load_json("mission_profile.json", {})
