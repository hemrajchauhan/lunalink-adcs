from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QFormLayout, QLabel, QGroupBox,
    QComboBox, QPushButton, QMessageBox,
)
from PyQt6.QtCore import pyqtSignal

from ....simulation.physics import orbit
from ....simulation.physics.constants import GM_EARTH, R_EARTH_M
from ....simulation.parameters import ADCSParams
from ....simulation.simulator import sizing_summary
from ....simulation.defaults import load_mission_profile
from ....simulation.repositories.satellite_repository import SatelliteRepository
from ....simulation.repositories.mission_repository import MissionRepository
from ...dialogs.add_mission_dialog import AddMissionDialog


class MissionTab(QWidget):
    """Browse / add missions (satellite + simulation parameters, all from JSON)
    and launch the ADCS simulation for the selected one."""

    simulateRequested = pyqtSignal(str)   # mission name

    def __init__(self, parent=None):
        super().__init__(parent)
        self._build_ui()
        self._reload_missions()

    def _build_ui(self):
        layout = QVBoxLayout(self)

        sel = QGroupBox("Mission")
        sform = QFormLayout(sel)
        self.mission_combo = QComboBox()
        self.mission_combo.currentTextChanged.connect(self._update)
        sform.addRow("Mission", self.mission_combo)
        self.desc_label = QLabel("—")
        self.desc_label.setWordWrap(True)
        sform.addRow("Description", self.desc_label)
        self.sat_label = QLabel("—")
        sform.addRow("Satellite", self.sat_label)
        self.parent_label = QLabel("—")
        sform.addRow("Orbits around", self.parent_label)

        buttons = QHBoxLayout()
        self.add_button = QPushButton("Add Mission…")
        self.add_button.clicked.connect(self._add_mission)
        self.delete_button = QPushButton("Delete")
        self.delete_button.clicked.connect(self._delete_mission)
        buttons.addWidget(self.add_button)
        buttons.addWidget(self.delete_button)
        sform.addRow(buttons)
        layout.addWidget(sel)

        orbit = QGroupBox("Orbit (derived)")
        oform = QFormLayout(orbit)
        self._orbit_labels = {}
        for key in ("Semi-major axis", "Eccentricity", "Perigee alt",
                    "Apogee alt", "Inclination", "Period"):
            lbl = QLabel("—")
            self._orbit_labels[key] = lbl
            oform.addRow(key, lbl)
        layout.addWidget(orbit)

        sc = QGroupBox("Spacecraft & actuator sizing (auto)")
        scform = QFormLayout(sc)
        self._sc_labels = {}
        for key in ("Mass", "Envelope", "Inertia (Ix,Iy,Iz)", "Slew torque",
                    "Slew momentum", "Recommended wheel hmax"):
            lbl = QLabel("—")
            self._sc_labels[key] = lbl
            scform.addRow(key, lbl)
        layout.addWidget(sc)

        sim = QGroupBox("Simulation parameters")
        simform = QFormLayout(sim)
        self._sim_labels = {}
        for key in ("Mode", "Initial tumble", "Magnetorquer", "Wheel capacity", "Duration"):
            lbl = QLabel("—")
            self._sim_labels[key] = lbl
            simform.addRow(key, lbl)
        layout.addWidget(sim)

        self.run_button = QPushButton("Run ADCS simulation  ▶")
        self.run_button.clicked.connect(self._run)
        layout.addWidget(self.run_button)

        profile = load_mission_profile()
        if profile:
            fixed = QGroupBox("Mission profile (fixed by brief)")
            fform = QFormLayout(fixed)
            fform.addRow("Ground station", QLabel(str(profile.get("ground_station", "—"))))
            fform.addRow("Downlink", QLabel(str(profile.get("earth_downlink", "—"))))
            fform.addRow("Power (EOL)", QLabel(f"{profile.get('power_budget_eol_kw', '—')} kW"))
            layout.addWidget(fixed)
        layout.addStretch()

    # ------------------------------------------------------------------
    def showEvent(self, event):
        self._reload_missions()
        super().showEvent(event)

    def _reload_missions(self):
        current = self.mission_combo.currentText()
        names = [m.name for m in MissionRepository().load_all()]
        self.mission_combo.blockSignals(True)
        self.mission_combo.clear()
        self.mission_combo.addItems(names)
        if current in names:
            self.mission_combo.setCurrentText(current)
        self.mission_combo.blockSignals(False)
        self._update(self.mission_combo.currentText())

    def _update(self, name):
        repo = MissionRepository()
        mission = repo.get_by_name(name) if name else None
        if mission is None:
            self.sat_label.setText("—")
            self.desc_label.setText("—")
            return
        sat = SatelliteRepository().get_by_name(mission.satellite)
        self.desc_label.setText(mission.description or "—")
        self.sat_label.setText(mission.satellite)
        if sat is None or sat.orbit is None:
            self.parent_label.setText("—")
            return

        o = sat.orbit
        a, e = o.semi_major_axis_m, o.eccentricity
        P = orbit.orbital_period_s(a, GM_EARTH)
        self.parent_label.setText(sat.parent or "—")
        self._orbit_labels["Semi-major axis"].setText(f"{a/1000:,.0f} km")
        self._orbit_labels["Eccentricity"].setText(f"{e:.4f}")
        self._orbit_labels["Perigee alt"].setText(f"{(a*(1-e)-R_EARTH_M)/1000:,.0f} km")
        self._orbit_labels["Apogee alt"].setText(f"{(a*(1+e)-R_EARTH_M)/1000:,.0f} km")
        self._orbit_labels["Inclination"].setText(f"{o.inclination_deg}°")
        self._orbit_labels["Period"].setText(f"{P/3600:.2f} h")

        params = repo.resolved_simulation_params(name)
        adcs_params = ADCSParams.from_mission(sat, params)
        dims = tuple(sat.dimensions_m)
        I = adcs_params.get_inertia()
        sizing = sizing_summary(adcs_params)
        self._sc_labels["Mass"].setText(f"{sat.mass_kg:.0f} kg")
        self._sc_labels["Envelope"].setText(f"{dims[0]} × {dims[1]} × {dims[2]} m")
        self._sc_labels["Inertia (Ix,Iy,Iz)"].setText(f"{I[0]:.0f}, {I[1]:.0f}, {I[2]:.0f} kg·m²")
        self._sc_labels["Slew torque"].setText(f"{sizing['slew_torque_nm']*1000:.1f} mN·m")
        self._sc_labels["Slew momentum"].setText(f"{sizing['slew_momentum_nms']:.2f} N·m·s")
        self._sc_labels["Recommended wheel hmax"].setText(
            f"{sizing['recommended_wheel_hmax_nms']:.1f} N·m·s")

        self._sim_labels["Mode"].setText(str(params.get("mode", "—")))
        self._sim_labels["Initial tumble"].setText(f"{params.get('initial_tumble_deg_s', 0)} °/s")
        self._sim_labels["Magnetorquer"].setText(f"{params.get('magnetorquer_max_dipole_am2', 0)} A·m²")
        self._sim_labels["Wheel capacity"].setText(f"{params.get('rw_max_momentum_nms', 0)} N·m·s")
        self._sim_labels["Duration"].setText(f"{params.get('n_orbits', 0):.0f} orbits")

    def _add_mission(self):
        dialog = AddMissionDialog(self)
        if dialog.exec():
            MissionRepository().add_mission(dialog.build_mission())
            self._reload_missions()
            self.mission_combo.setCurrentText(dialog.name_edit.text().strip())

    def _delete_mission(self):
        name = self.mission_combo.currentText()
        if not name:
            return
        if QMessageBox.question(self, "Delete mission", f"Delete '{name}'?") \
                == QMessageBox.StandardButton.Yes:
            MissionRepository().delete_mission(name)
            self._reload_missions()

    def _run(self):
        name = self.mission_combo.currentText()
        if name:
            self.simulateRequested.emit(name)
