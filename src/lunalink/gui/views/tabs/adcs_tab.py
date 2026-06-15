import numpy as np
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QFormLayout, QGroupBox, QDoubleSpinBox, QComboBox,
    QPushButton, QLabel,
)
from PyQt6.QtCore import pyqtSignal

from ....simulation.parameters import ADCSParams
from ....simulation.physics.dynamics import box_inertia
from ....simulation.repositories.satellite_repository import SatelliteRepository
from ....simulation.repositories.mission_repository import MissionRepository

_MODE_KEYS = ["detumble", "sun_pointing", "full"]
_MODE_LABELS = ["Detumble (B-dot)", "Sun-pointing (PD + wheels)",
                "Full mission (detumble → pointing)"]


def _spin(minimum, maximum, value, decimals=2, step=1.0, suffix=""):
    box = QDoubleSpinBox()
    box.setRange(minimum, maximum)
    box.setDecimals(decimals)
    box.setSingleStep(step)
    box.setValue(value)
    if suffix:
        box.setSuffix(suffix)
    return box


class ADCSTab(QWidget):
    """Pick a mission (which carries the satellite + simulation parameters from
    JSON), optionally tweak, then run. Emits ``parametersChanged``."""

    parametersChanged = pyqtSignal(object)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._satellite = None
        self._build_ui()
        self._reload_missions()

    def _build_ui(self):
        layout = QVBoxLayout(self)

        target = QGroupBox("Mission")
        tform = QFormLayout(target)
        self.mission_combo = QComboBox()
        self.mission_combo.currentTextChanged.connect(self._on_mission_changed)
        self.sat_label = QLabel("—")
        tform.addRow("Mission", self.mission_combo)
        tform.addRow("Satellite", self.sat_label)
        layout.addWidget(target)

        sc = QGroupBox("Spacecraft / initial state")
        sc_form = QFormLayout(sc)
        self.ix = _spin(1, 100000, 135, step=10, suffix=" kg·m²")
        self.iy = _spin(1, 100000, 208, step=10, suffix=" kg·m²")
        self.iz = _spin(1, 100000, 260, step=10, suffix=" kg·m²")
        self.tumble = _spin(0, 60, 10, decimals=1, step=0.5, suffix=" °/s")
        sc_form.addRow("Inertia Ix (auto)", self.ix)
        sc_form.addRow("Inertia Iy (auto)", self.iy)
        sc_form.addRow("Inertia Iz (auto)", self.iz)
        sc_form.addRow("Initial tumble rate", self.tumble)
        layout.addWidget(sc)

        act = QGroupBox("Actuators")
        act_form = QFormLayout(act)
        self.dipole = _spin(1, 500, 50, decimals=1, step=5, suffix=" A·m²")
        self.rw_max = _spin(0.1, 200, 4, decimals=1, step=0.5, suffix=" N·m·s")
        act_form.addRow("Magnetorquer dipole", self.dipole)
        act_form.addRow("Reaction-wheel capacity", self.rw_max)
        layout.addWidget(act)

        scen = QGroupBox("Scenario")
        scen_form = QFormLayout(scen)
        self.mode = QComboBox()
        self.mode.addItems(_MODE_LABELS)
        self.n_orbits = _spin(1, 20, 3, decimals=0, step=1, suffix=" orbits")
        scen_form.addRow("Mode", self.mode)
        scen_form.addRow("Simulated duration", self.n_orbits)
        layout.addWidget(scen)

        self.run_button = QPushButton("Run simulation")
        self.run_button.clicked.connect(self._emit_params)
        layout.addWidget(self.run_button)

        self.status = QLabel("")
        self.status.setStyleSheet("color: #6fae6f;")
        layout.addWidget(self.status)
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
        if self.mission_combo.currentText():
            self._on_mission_changed(self.mission_combo.currentText())

    def _on_mission_changed(self, name):
        if not name:
            return
        repo = MissionRepository()
        mission = repo.get_by_name(name)
        if mission is None:
            return
        params = repo.resolved_simulation_params(name)
        self._satellite = SatelliteRepository().get_by_name(mission.satellite)
        self.sat_label.setText(mission.satellite)

        # Populate editable widgets from the mission's parameters.
        self.tumble.setValue(params.get("initial_tumble_deg_s", 10.0))
        self.dipole.setValue(params.get("magnetorquer_max_dipole_am2", 50.0))
        self.rw_max.setValue(params.get("rw_max_momentum_nms", 4.0))
        self.n_orbits.setValue(params.get("n_orbits", 3.0))
        mode = params.get("mode", "detumble")
        if mode in _MODE_KEYS:
            self.mode.setCurrentIndex(_MODE_KEYS.index(mode))

        if self._satellite is not None:
            I = box_inertia(self._satellite.mass_kg, tuple(self._satellite.dimensions_m))
            for spin, val in zip((self.ix, self.iy, self.iz), I):
                spin.blockSignals(True)
                spin.setValue(float(val))
                spin.blockSignals(False)

    def select_mission(self, name):
        self._reload_missions()
        if name:
            self.mission_combo.setCurrentText(name)

    def run_now(self):
        self._emit_params()

    def get_params(self) -> ADCSParams:
        name = self.mission_combo.currentText()
        params = MissionRepository().resolved_simulation_params(name) if name else {}
        # Apply any live edits from the widgets.
        params.update({
            "initial_tumble_deg_s": self.tumble.value(),
            "magnetorquer_max_dipole_am2": self.dipole.value(),
            "rw_max_momentum_nms": self.rw_max.value(),
            "n_orbits": self.n_orbits.value(),
            "mode": _MODE_KEYS[self.mode.currentIndex()],
        })
        adcs_params = ADCSParams.from_mission(self._satellite, params)
        # Honour manual inertia overrides from the spin boxes.
        adcs_params.inertia = np.array([self.ix.value(), self.iy.value(), self.iz.value()])
        return adcs_params

    def _emit_params(self):
        self.status.setText(f"Simulation updated for {self.mission_combo.currentText()}.")
        self.parametersChanged.emit(self.get_params())
