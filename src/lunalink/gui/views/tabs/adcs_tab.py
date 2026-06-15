import numpy as np
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QFormLayout, QGroupBox, QDoubleSpinBox, QComboBox,
    QPushButton, QLabel,
)
from PyQt6.QtCore import pyqtSignal

from ....simulation.adcs import ADCSParams


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
    """Controls for the ADCS simulation. Emits ``parametersChanged`` (with an
    ``ADCSParams``) when the user runs the simulation."""

    parametersChanged = pyqtSignal(object)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)

        sc = QGroupBox("Spacecraft / initial state")
        sc_form = QFormLayout(sc)
        self.ix = _spin(1, 100000, 135, step=10, suffix=" kg·m²")
        self.iy = _spin(1, 100000, 208, step=10, suffix=" kg·m²")
        self.iz = _spin(1, 100000, 260, step=10, suffix=" kg·m²")
        self.tumble = _spin(0, 60, 10, decimals=1, step=0.5, suffix=" °/s")
        sc_form.addRow("Inertia Ix", self.ix)
        sc_form.addRow("Inertia Iy", self.iy)
        sc_form.addRow("Inertia Iz", self.iz)
        sc_form.addRow("Initial tumble rate", self.tumble)
        layout.addWidget(sc)

        act = QGroupBox("Actuators")
        act_form = QFormLayout(act)
        self.dipole = _spin(1, 500, 30, decimals=1, step=5, suffix=" A·m²")
        self.rw_max = _spin(0.1, 200, 12, decimals=1, step=1, suffix=" N·m·s")
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

    def get_params(self) -> ADCSParams:
        return ADCSParams(
            inertia=np.array([self.ix.value(), self.iy.value(), self.iz.value()]),
            initial_tumble_deg_s=self.tumble.value(),
            magnetorquer_max_dipole_am2=self.dipole.value(),
            rw_max_momentum_nms=self.rw_max.value(),
            n_orbits=self.n_orbits.value(),
            mode=self._mode_keys[self.mode.currentIndex()],
        )

    def _emit_params(self):
        self.status.setText("Simulation updated.")
        self.parametersChanged.emit(self.get_params())
