import numpy as np
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QFormLayout, QGroupBox, QDoubleSpinBox, QComboBox,
    QPushButton, QLabel,
)
from PyQt6.QtCore import pyqtSignal

from ....simulation.adcs import ADCSParams, box_inertia
from ....simulation.objects import OrbitElements
from ....simulation.repositories.satellite_repository import SatelliteRepository


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
    """ADCS simulation controls. The satellite selector drives the simulated
    orbit and (auto) inertia; the rest are control/actuator parameters."""

    parametersChanged = pyqtSignal(object)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._orbit = OrbitElements(24_628_137.0, 0.7207, 63.4, 0.0, 270.0, 0.0)
        self._build_ui()
        self._reload_satellites()

    def _build_ui(self):
        layout = QVBoxLayout(self)

        target = QGroupBox("Simulated satellite")
        tform = QFormLayout(target)
        self.sat_combo = QComboBox()
        self.sat_combo.currentTextChanged.connect(self._on_satellite_changed)
        tform.addRow("Satellite", self.sat_combo)
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
        self.dipole = _spin(1, 500, 30, decimals=1, step=5, suffix=" A·m²")
        self.rw_max = _spin(0.1, 200, 4, decimals=1, step=0.5, suffix=" N·m·s")
        act_form.addRow("Magnetorquer dipole", self.dipole)
        act_form.addRow("Reaction-wheel capacity", self.rw_max)
        layout.addWidget(act)

        scen = QGroupBox("Scenario")
        scen_form = QFormLayout(scen)
        self.mode = QComboBox()
        self.mode.addItems([
            "Detumble (B-dot)",
            "Sun-pointing (PD + wheels)",
            "Full mission (detumble → pointing)",
        ])
        self._mode_keys = ["detumble", "sun_pointing", "full"]
        self.mode.setCurrentIndex(1)
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
        self._reload_satellites()
        super().showEvent(event)

    def _reload_satellites(self):
        current = self.sat_combo.currentText()
        names = [s.name for s in SatelliteRepository().load_all()]
        self.sat_combo.blockSignals(True)
        self.sat_combo.clear()
        self.sat_combo.addItems(names)
        if current in names:
            self.sat_combo.setCurrentText(current)
        self.sat_combo.blockSignals(False)
        if self.sat_combo.currentText():
            self._on_satellite_changed(self.sat_combo.currentText())

    def _on_satellite_changed(self, name):
        sat = SatelliteRepository().get_by_name(name) if name else None
        if sat is None or sat.orbit is None:
            return
        self._orbit = sat.orbit
        I = box_inertia(sat.mass_kg, tuple(sat.dimensions_m))
        for spin, val in zip((self.ix, self.iy, self.iz), I):
            spin.blockSignals(True)
            spin.setValue(float(val))
            spin.blockSignals(False)

    def select_satellite(self, name):
        self._reload_satellites()
        if name:
            self.sat_combo.setCurrentText(name)

    def run_now(self):
        self._emit_params()

    def get_params(self) -> ADCSParams:
        o = self._orbit
        return ADCSParams(
            inertia=np.array([self.ix.value(), self.iy.value(), self.iz.value()]),
            initial_tumble_deg_s=self.tumble.value(),
            magnetorquer_max_dipole_am2=self.dipole.value(),
            rw_max_momentum_nms=self.rw_max.value(),
            n_orbits=self.n_orbits.value(),
            mode=self._mode_keys[self.mode.currentIndex()],
            semi_major_axis_m=o.semi_major_axis_m,
            eccentricity=o.eccentricity,
            inclination_deg=o.inclination_deg,
            raan_deg=o.raan_deg,
            arg_periapsis_deg=o.arg_periapsis_deg,
            mean_anomaly_epoch_deg=o.mean_anomaly_epoch_deg,
        )

    def _emit_params(self):
        self.status.setText(f"Simulation updated for {self.sat_combo.currentText()}.")
        self.parametersChanged.emit(self.get_params())
