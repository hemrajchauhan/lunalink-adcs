"""Dialog for adding a mission: a named ADCS scenario that links a satellite
to a set of simulation parameters. Saved to missions.json.
"""
from PyQt6.QtWidgets import (
    QDialog, QComboBox, QLineEdit, QDoubleSpinBox, QPushButton, QFormLayout,
    QVBoxLayout, QDialogButtonBox, QMessageBox,
)

from ...simulation.objects import Mission
from ...simulation.defaults import load_simulation_defaults
from ...simulation.repositories.satellite_repository import SatelliteRepository

_MODE_LABELS = ["Detumble (B-dot)", "Sun-pointing (PD + wheels)",
                "Full mission (detumble → pointing)",
                "Slew (rest-to-rest)"]
_MODE_KEYS = ["detumble", "sun_pointing", "full", "slew"]


def _spin(minimum, maximum, value, decimals=1, step=1.0):
    """Numeric input; units go in the row label, not in the editable field."""
    box = QDoubleSpinBox()
    box.setRange(minimum, maximum)
    box.setDecimals(decimals)
    box.setSingleStep(step)
    box.setValue(value)
    return box


class AddMissionDialog(QDialog):

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Add Mission")
        self.setMinimumWidth(380)
        self._defaults = load_simulation_defaults()
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        form = QFormLayout()

        self.name_edit = QLineEdit()
        self.sat_combo = QComboBox()
        self.sat_combo.addItems([s.name for s in SatelliteRepository().load_all()])
        self.desc_edit = QLineEdit()

        self.mode = QComboBox()
        self.mode.addItems(_MODE_LABELS)
        idx = _MODE_KEYS.index(self._defaults.get("mode", "detumble")) \
            if self._defaults.get("mode") in _MODE_KEYS else 0
        self.mode.setCurrentIndex(idx)

        self.tumble = _spin(0, 60, self._defaults["initial_tumble_deg_s"],
                            step=0.5)
        self.dipole = _spin(1, 500, self._defaults["magnetorquer_max_dipole_am2"],
                            step=5)
        self.rw_max = _spin(0.1, 200, self._defaults["rw_max_momentum_nms"],
                            step=0.5)
        self.n_orbits = _spin(1, 20, self._defaults["n_orbits"],
                              decimals=0, step=1)

        form.addRow("Name", self.name_edit)
        form.addRow("Satellite", self.sat_combo)
        form.addRow("Description", self.desc_edit)
        form.addRow("Mode", self.mode)
        form.addRow("Initial tumble [°/s]", self.tumble)
        form.addRow("Magnetorquer dipole [A·m²]", self.dipole)
        form.addRow("Reaction-wheel capacity [N·m·s]", self.rw_max)
        form.addRow("Duration [orbits]", self.n_orbits)
        layout.addLayout(form)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(self._on_accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def _on_accept(self):
        if not self.name_edit.text().strip():
            QMessageBox.warning(self, "Missing name", "Please enter a mission name.")
            return
        if not self.sat_combo.currentText():
            QMessageBox.warning(self, "No satellite",
                                "Add a satellite first (Objects tab).")
            return
        self.accept()

    def build_mission(self) -> Mission:
        return Mission(
            name=self.name_edit.text().strip(),
            satellite=self.sat_combo.currentText(),
            description=self.desc_edit.text().strip(),
            simulation={
                "mode": _MODE_KEYS[self.mode.currentIndex()],
                "initial_tumble_deg_s": self.tumble.value(),
                "magnetorquer_max_dipole_am2": self.dipole.value(),
                "rw_max_momentum_nms": self.rw_max.value(),
                "n_orbits": self.n_orbits.value(),
            },
        )
