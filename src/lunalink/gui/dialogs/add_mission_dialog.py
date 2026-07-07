"""Dialog for adding a mission: a named ADCS scenario that links a satellite
to a set of simulation parameters. Saved to missions.json.
"""
from PyQt6.QtWidgets import (
    QDialog, QComboBox, QLineEdit, QDoubleSpinBox, QPushButton, QFormLayout,
    QVBoxLayout, QDialogButtonBox, QMessageBox, QLabel,
)

from ...simulation.objects import Mission
from ...simulation.defaults import load_simulation_defaults
from ...simulation.repositories.satellite_repository import SatelliteRepository

_MODE_LABELS = ["Detumble", "Sun-pointing", "Full mission", "Slew maneuver"]
_MODE_KEYS = ["detumble", "sun_pointing", "full", "slew"]


def _spin(minimum, maximum, value, decimals=1, step=1.0, tip=""):
    """Numeric input; units go in the row label, not in the editable field."""
    box = QDoubleSpinBox()
    box.setRange(minimum, maximum)
    box.setDecimals(decimals)
    box.setSingleStep(step)
    box.setValue(value)
    if tip:
        box.setToolTip(tip)
    return box


def _labeled(text: str, tip: str) -> QLabel:
    """A form-row label that shows an explanatory tooltip on hover."""
    label = QLabel(text)
    label.setToolTip(tip)
    return label


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

        self.tumble = _spin(0, 60, self._defaults["initial_tumble_deg_s"], step=0.5,
                            tip="Initial spin rate for the detumble and full-"
                                "mission scenarios.")
        self.dipole = _spin(1, 500, self._defaults["magnetorquer_max_dipole_am2"],
                            step=5, tip="Maximum magnetic dipole the torque rods "
                                        "can produce.")
        self.rw_max = _spin(0.1, 200, self._defaults["rw_max_momentum_nms"], step=0.5,
                            tip="Maximum angular momentum each reaction wheel can "
                                "store before it must be desaturated.")
        self.n_orbits = _spin(1, 100000, self._defaults["n_orbits"],
                              decimals=0, step=1,
                              tip="How many orbits the run covers. Large values "
                                  "take longer to compute.")

        self.name_edit.setToolTip("A unique name for this mission preset.")
        self.sat_combo.setToolTip("The spacecraft this mission flies.")
        self.desc_edit.setToolTip("A short description of the mission.")
        self.mode.setToolTip("Default control scenario for this mission.")

        form.addRow(_labeled("Name", "A unique name for this mission preset."),
                    self.name_edit)
        form.addRow(_labeled("Satellite", "The spacecraft this mission flies."),
                    self.sat_combo)
        form.addRow(_labeled("Description", "A short description of the mission."),
                    self.desc_edit)
        form.addRow(_labeled("Mode", "Default control scenario (detumble, "
                             "sun-pointing, full mission, or slew)."), self.mode)
        form.addRow(_labeled("Initial tumble [°/s]",
                    "Initial spin rate for the detumble and full-mission "
                    "scenarios."), self.tumble)
        form.addRow(_labeled("Magnetorquer dipole [A·m²]",
                    "Maximum magnetic dipole the torque rods can produce."),
                    self.dipole)
        form.addRow(_labeled("Reaction-wheel capacity [N·m·s]",
                    "Maximum angular momentum each reaction wheel can store."),
                    self.rw_max)
        form.addRow(_labeled("Duration [orbits]",
                    "How many orbits the run covers. Large values take longer."),
                    self.n_orbits)
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
