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

_MODE_KEYS = ["detumble", "sun_pointing", "full", "slew"]
_MODE_LABELS = ["Detumble", "Sun-pointing", "Full mission", "Slew maneuver"]
_MODE_TOOLTIP = (
    "Detumble: null out an initial spin using magnetorquers.\n"
    "Sun-pointing: hold a body axis on the Sun with reaction wheels.\n"
    "Full mission: detumble first, then acquire and hold Sun-pointing.\n"
    "Slew maneuver: a rest-to-rest reorientation by a commanded angle."
)


def _spin(minimum, maximum, value, decimals=2, step=1.0):
    """Numeric input. Units belong in the row label, not inside the editable
    field, so the number can be selected and typed over directly."""
    box = QDoubleSpinBox()
    box.setRange(minimum, maximum)
    box.setDecimals(decimals)
    box.setSingleStep(step)
    box.setValue(value)
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
        self.mission_combo.setToolTip("Mission to simulate. Its parameters fill in "
                                      "the fields below, which you can fine-tune.")
        self.mission_combo.currentTextChanged.connect(self._on_mission_changed)
        self.sat_label = QLabel("Not selected")
        tform.addRow("Mission", self.mission_combo)
        tform.addRow("Spacecraft", self.sat_label)
        layout.addWidget(target)

        sc = QGroupBox("Spacecraft and Initial State")
        sc_form = QFormLayout(sc)
        self.ix = _spin(1, 100000, 135, step=10)
        self.iy = _spin(1, 100000, 208, step=10)
        self.iz = _spin(1, 100000, 260, step=10)
        self.tumble = _spin(0, 60, 10, decimals=1, step=0.5)
        for box, axis in ((self.ix, "X"), (self.iy, "Y"), (self.iz, "Z")):
            box.setToolTip(f"Resistance to rotation about the body {axis} axis "
                           "(filled from the spacecraft mass and dimensions).")
        self.tumble.setToolTip("How fast the spacecraft is spinning at the start "
                               "of the run.")
        sc_form.addRow("Moment of inertia X [kg·m²]", self.ix)
        sc_form.addRow("Moment of inertia Y [kg·m²]", self.iy)
        sc_form.addRow("Moment of inertia Z [kg·m²]", self.iz)
        sc_form.addRow("Initial tumble rate [°/s]", self.tumble)
        layout.addWidget(sc)

        act = QGroupBox("Actuators")
        act_form = QFormLayout(act)
        self.dipole = _spin(1, 500, 50, decimals=1, step=5)
        self.rw_max = _spin(0.1, 200, 4, decimals=1, step=0.5)
        self.rw_torque = _spin(0.001, 5, 0.05, decimals=3, step=0.01)
        self.dipole.setToolTip("Maximum magnetic dipole the torque rods can produce "
                               "(used for detumbling and wheel desaturation).")
        self.rw_max.setToolTip("Maximum angular momentum each reaction wheel can "
                               "store before it saturates and must be desaturated.")
        self.rw_torque.setToolTip("Maximum torque each reaction wheel can apply. "
                                  "Limits how aggressively the spacecraft can turn.")
        act_form.addRow("Magnetorquer strength [A·m²]", self.dipole)
        act_form.addRow("Reaction-wheel capacity [N·m·s]", self.rw_max)
        act_form.addRow("Reaction-wheel max torque [N·m]", self.rw_torque)
        layout.addWidget(act)

        scen = QGroupBox("Scenario")
        scen_form = QFormLayout(scen)
        self.mode = QComboBox()
        self.mode.addItems(_MODE_LABELS)
        self.mode.setToolTip(_MODE_TOOLTIP)
        self.mode.currentIndexChanged.connect(self._on_mode_changed)
        self.n_orbits = _spin(1, 20, 3, decimals=0, step=1)
        self.n_orbits.setToolTip("How many orbits the simulation covers "
                                 "(not used for a slew, which is a short event).")
        self.slew_angle = _spin(1, 180, 90, decimals=0, step=5)
        self.slew_angle.setToolTip("Angle of the rest-to-rest reorientation "
                                   "(only used in Slew maneuver mode).")
        scen_form.addRow("Control mode", self.mode)
        scen_form.addRow("Simulated duration [orbits]", self.n_orbits)
        scen_form.addRow("Slew angle [°]", self.slew_angle)
        layout.addWidget(scen)

        self.run_button = QPushButton("Run Simulation")
        self.run_button.setToolTip("Run the ADCS simulation with the settings above. "
                                   "Results appear in the plot tabs below.")
        self.run_button.clicked.connect(self._emit_params)
        layout.addWidget(self.run_button)

        self.status = QLabel("")
        self.status.setWordWrap(True)
        self.status.setStyleSheet("color: #6fae6f;")
        layout.addWidget(self.status)
        layout.addStretch()
        self._on_mode_changed(self.mode.currentIndex())

    # ------------------------------------------------------------------
    def _on_mode_changed(self, index):
        """Enable only the fields that the selected scenario actually uses."""
        is_slew = _MODE_KEYS[index] == "slew"
        self.n_orbits.setEnabled(not is_slew)
        self.slew_angle.setEnabled(is_slew)
        uses_tumble = _MODE_KEYS[index] in ("detumble", "full")
        self.tumble.setEnabled(uses_tumble)

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
        self.rw_torque.setValue(params.get("rw_max_torque_nm", 0.05))
        self.slew_angle.setValue(params.get("slew_angle_deg", 90.0))
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

    @property
    def current_satellite_name(self) -> str | None:
        """Name of the spacecraft of the selected mission (drives the 3D
        attitude animation after a run)."""
        return self._satellite.name if self._satellite is not None else None

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
            "rw_max_torque_nm": self.rw_torque.value(),
            "slew_angle_deg": self.slew_angle.value(),
            "n_orbits": self.n_orbits.value(),
            "mode": _MODE_KEYS[self.mode.currentIndex()],
        })
        adcs_params = ADCSParams.from_mission(self._satellite, params)
        # Honour manual inertia overrides from the spin boxes.
        adcs_params.inertia = np.array([self.ix.value(), self.iy.value(), self.iz.value()])
        return adcs_params

    def _emit_params(self):
        self.status.setStyleSheet("color: #cfd6e4;")
        self.status.setText(f"Running simulation for "
                            f"{self.mission_combo.currentText()}…")
        self.status.repaint()
        self.parametersChanged.emit(self.get_params())

    # -- result feedback (called by the controller after each run) --------
    def show_run_summary(self, result: dict):
        """One-line result summary under the Run button."""
        parts = []
        acquire = result.get("t_acquire_h")
        mode = result.get("mode", "")
        if mode == "slew" and result.get("slew"):
            s = result["slew"]
            settle = s.get("settle_time_s")
            parts.append(f"slew settled in {settle:.0f} s" if settle is not None
                         else "slew did not settle in the window")
            parts.append(f"peak wheel momentum {s['peak_wheel_nms']:.2f} N·m·s")
        else:
            if acquire is not None:
                parts.append(f"target acquired after {acquire:.2f} h")
            elif mode in ("full", "detumble"):
                parts.append("still detumbling at the end of the run "
                             "(try more orbits)")
            err = result.get("attitude_error_deg")
            if err is not None and len(err) and mode != "detumble":
                parts.append(f"final pointing error {err[-1]:.3f}°")
            om = result.get("omega_mag_deg_s")
            if om is not None and len(om) and mode in ("detumble", "full"):
                parts.append(f"final rate {om[-1]:.2f} °/s")
        self.status.setStyleSheet("color: #6fae6f;")
        self.status.setText("Done: " + ";  ".join(parts))

    def show_run_error(self, message: str):
        self.status.setStyleSheet("color: #e06c75;")
        self.status.setText(f"Simulation failed: {message}")
