from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QFormLayout, QLabel, QGroupBox,
)

from ...simulation.physics import orbit
from ...simulation.physics.constants import GM_EARTH, R_EARTH_M
from ...simulation.parameters import ADCSParams
from ...simulation.simulator import sizing_summary
from ...simulation.defaults import load_mission_profile
from ...simulation.repositories.satellite_repository import SatelliteRepository
from ...simulation.repositories.mission_repository import MissionRepository


class MissionInfoPanel(QWidget):
    """Read-only summary of the selected mission: its orbit, spacecraft and
    actuator sizing, simulation settings and the fixed mission requirements.
    Everything here is computed from the mission and cannot be edited (edit a
    mission from the Mission tab or the Objects tab)."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._build_ui()

    def _labelled(self, tooltip=""):
        lbl = QLabel("Not selected")
        if tooltip:
            lbl.setToolTip(tooltip)
        return lbl

    def _build_ui(self):
        # No internal scroll area: the hosting view (the Mission tab) provides
        # one scrollable column, avoiding nested scroll bars.
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        heading = QLabel("Mission Details")
        heading.setStyleSheet("font-weight: 600; font-size: 13px; padding: 2px;")
        layout.addWidget(heading)

        # -- Orbit -------------------------------------------------------
        orbit_box = QGroupBox("Orbit")
        orbit_box.setToolTip("The orbit the spacecraft flies, computed from its "
                             "orbital elements.")
        oform = QFormLayout(orbit_box)
        self._orbit = {}
        orbit_rows = [
            ("Semi-major axis", "Average of the closest and farthest orbit radius."),
            ("Eccentricity", "How stretched the orbit is (0 = circle, closer to 1 = "
                             "very elongated)."),
            ("Perigee altitude", "Height above Earth's surface at the closest point."),
            ("Apogee altitude", "Height above Earth's surface at the farthest point."),
            ("Inclination", "Tilt of the orbit plane relative to the equator."),
            ("Orbital period", "Time to complete one full orbit."),
        ]
        for key, tip in orbit_rows:
            lbl = self._labelled(tip)
            self._orbit[key] = lbl
            row = QLabel(key)
            row.setToolTip(tip)
            oform.addRow(row, lbl)
        layout.addWidget(orbit_box)

        # -- Spacecraft & sizing ----------------------------------------
        sc_box = QGroupBox("Spacecraft and Actuator Sizing")
        sc_box.setToolTip("Physical properties of the spacecraft and the actuator "
                          "sizes the analysis recommends.")
        scform = QFormLayout(sc_box)
        self._sc = {}
        sc_rows = [
            ("Mass", "Total spacecraft mass."),
            ("Body dimensions", "Length, width and height of the spacecraft body."),
            ("Moments of inertia", "Resistance to rotation about each body axis "
                                   "(X, Y, Z)."),
            ("Slew control torque", "Torque the wheels must provide to reorient "
                                    "the spacecraft."),
            ("Peak slew momentum", "Angular momentum the wheels must absorb during "
                                   "a reorientation."),
            ("Recommended wheel capacity", "Suggested reaction-wheel momentum "
                                           "capacity for this mission."),
        ]
        for key, tip in sc_rows:
            lbl = self._labelled(tip)
            self._sc[key] = lbl
            row = QLabel(key)
            row.setToolTip(tip)
            scform.addRow(row, lbl)
        layout.addWidget(sc_box)

        # -- Simulation settings ----------------------------------------
        sim_box = QGroupBox("Simulation Settings")
        sim_box.setToolTip("The scenario the simulation will run for this mission.")
        simform = QFormLayout(sim_box)
        self._sim = {}
        sim_rows = [
            ("Control mode", "Which control law the simulation uses."),
            ("Initial tumble rate", "How fast the spacecraft is spinning at the "
                                    "start."),
            ("Magnetorquer strength", "Maximum magnetic dipole the torque rods can "
                                      "produce."),
            ("Reaction-wheel capacity", "Maximum angular momentum a wheel can store."),
            ("Simulated duration", "How many orbits the run covers."),
        ]
        for key, tip in sim_rows:
            lbl = self._labelled(tip)
            self._sim[key] = lbl
            row = QLabel(key)
            row.setToolTip(tip)
            simform.addRow(row, lbl)
        layout.addWidget(sim_box)

        # -- Fixed mission profile --------------------------------------
        profile = load_mission_profile()
        if profile:
            prof_box = QGroupBox("Mission Profile")
            prof_box.setToolTip("Fixed requirements set by the mission brief.")
            pform = QFormLayout(prof_box)
            pform.addRow("Ground station",
                         QLabel(str(profile.get("ground_station", "Not set"))))
            pform.addRow("Earth downlink",
                         QLabel(str(profile.get("earth_downlink", "Not set"))))
            pform.addRow("Power at end of life",
                         QLabel(f"{profile.get('power_budget_eol_kw', 'Not set')} kW"))
            layout.addWidget(prof_box)

        layout.addStretch()

    # ------------------------------------------------------------------
    def update_for_mission(self, name: str):
        repo = MissionRepository()
        mission = repo.get_by_name(name) if name else None
        if mission is None:
            return
        sat = SatelliteRepository().get_by_name(mission.satellite)
        if sat is None or sat.orbit is None:
            return

        o = sat.orbit
        a, e = o.semi_major_axis_m, o.eccentricity
        P = orbit.orbital_period_s(a, GM_EARTH)
        self._orbit["Semi-major axis"].setText(f"{a/1000:,.0f} km")
        self._orbit["Eccentricity"].setText(f"{e:.4f}")
        self._orbit["Perigee altitude"].setText(f"{(a*(1-e)-R_EARTH_M)/1000:,.0f} km")
        self._orbit["Apogee altitude"].setText(f"{(a*(1+e)-R_EARTH_M)/1000:,.0f} km")
        self._orbit["Inclination"].setText(f"{o.inclination_deg}°")
        self._orbit["Orbital period"].setText(f"{P/3600:.2f} h")

        params = repo.resolved_simulation_params(name)
        adcs_params = ADCSParams.from_mission(sat, params)
        dims = tuple(sat.dimensions_m)
        I = adcs_params.get_inertia()
        sizing = sizing_summary(adcs_params)
        self._sc["Mass"].setText(f"{sat.mass_kg:.0f} kg")
        self._sc["Body dimensions"].setText(f"{dims[0]} × {dims[1]} × {dims[2]} m")
        self._sc["Moments of inertia"].setText(
            f"{I[0]:.0f}, {I[1]:.0f}, {I[2]:.0f} kg·m²")
        self._sc["Slew control torque"].setText(f"{sizing['slew_torque_nm']*1000:.1f} mN·m")
        self._sc["Peak slew momentum"].setText(f"{sizing['slew_momentum_nms']:.2f} N·m·s")
        self._sc["Recommended wheel capacity"].setText(
            f"{sizing['recommended_wheel_hmax_nms']:.1f} N·m·s")

        mode_names = {"detumble": "Detumble", "sun_pointing": "Sun-pointing",
                      "full": "Full mission", "slew": "Slew maneuver"}
        mode = params.get("mode", "")
        self._sim["Control mode"].setText(mode_names.get(mode, mode or "Not set"))
        self._sim["Initial tumble rate"].setText(
            f"{params.get('initial_tumble_deg_s', 0)} °/s")
        self._sim["Magnetorquer strength"].setText(
            f"{params.get('magnetorquer_max_dipole_am2', 0)} A·m²")
        self._sim["Reaction-wheel capacity"].setText(
            f"{params.get('rw_max_momentum_nms', 0)} N·m·s")
        self._sim["Simulated duration"].setText(
            f"{params.get('n_orbits', 0):.0f} orbits")
