from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QFormLayout, QLabel, QGroupBox, QComboBox, QPushButton,
)
from PyQt6.QtCore import pyqtSignal

from .... import config
from ....config import GM_EARTH
from ....simulation import orbits
from ....simulation.adcs import box_inertia, sizing_summary, ADCSParams
from ....simulation.repositories.satellite_repository import SatelliteRepository

R_EARTH_M = 6.378e6


class MissionTab(QWidget):
    """One place that ties a satellite to its parent body, derived orbit,
    spacecraft mass properties and (auto) actuator sizing - and runs the
    ADCS simulation for it."""

    simulateRequested = pyqtSignal(str)   # satellite name

    def __init__(self, parent=None):
        super().__init__(parent)
        self._build_ui()
        self._reload_satellites()

    def _build_ui(self):
        layout = QVBoxLayout(self)

        sel = QGroupBox("Mission")
        sform = QFormLayout(sel)
        self.sat_combo = QComboBox()
        self.sat_combo.currentTextChanged.connect(self._update)
        sform.addRow("Satellite", self.sat_combo)
        self.parent_label = QLabel("—")
        sform.addRow("Orbits around", self.parent_label)
        layout.addWidget(sel)

        orbit = QGroupBox("Orbit (derived)")
        oform = QFormLayout(orbit)
        self._orbit_labels = {}
        for key in ("Semi-major axis", "Eccentricity", "Perigee alt", "Apogee alt",
                    "Inclination", "Period"):
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

        self.run_button = QPushButton("Run ADCS simulation  ▶")
        self.run_button.clicked.connect(self._run)
        layout.addWidget(self.run_button)

        fixed = QGroupBox("Mission constants (fixed by brief)")
        fform = QFormLayout(fixed)
        fform.addRow("Ground station", QLabel(config.GROUND_STATION))
        fform.addRow("Downlink", QLabel(config.EARTH_DOWNLINK))
        fform.addRow("Power (EOL)", QLabel(f"{config.POWER_BUDGET_EOL} kW"))
        layout.addWidget(fixed)
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
        self._update(self.sat_combo.currentText())

    def _update(self, name):
        sat = SatelliteRepository().get_by_name(name) if name else None
        if sat is None or sat.orbit is None:
            self.parent_label.setText("—")
            return
        o = sat.orbit
        a, e = o.semi_major_axis_m, o.eccentricity
        mu = GM_EARTH if sat.parent == "Earth" else GM_EARTH
        P = orbits.orbital_period_s(a, mu)
        self.parent_label.setText(sat.parent or "—")
        self._orbit_labels["Semi-major axis"].setText(f"{a/1000:,.0f} km")
        self._orbit_labels["Eccentricity"].setText(f"{e:.4f}")
        self._orbit_labels["Perigee alt"].setText(f"{(a*(1-e)-R_EARTH_M)/1000:,.0f} km")
        self._orbit_labels["Apogee alt"].setText(f"{(a*(1+e)-R_EARTH_M)/1000:,.0f} km")
        self._orbit_labels["Inclination"].setText(f"{o.inclination_deg}°")
        self._orbit_labels["Period"].setText(f"{P/3600:.2f} h")

        dims = tuple(sat.dimensions_m)
        I = box_inertia(sat.mass_kg, dims)
        sizing = sizing_summary(ADCSParams(mass_kg=sat.mass_kg, dims_m=dims))
        self._sc_labels["Mass"].setText(f"{sat.mass_kg:.0f} kg")
        self._sc_labels["Envelope"].setText(f"{dims[0]} × {dims[1]} × {dims[2]} m")
        self._sc_labels["Inertia (Ix,Iy,Iz)"].setText(
            f"{I[0]:.0f}, {I[1]:.0f}, {I[2]:.0f} kg·m²")
        self._sc_labels["Slew torque"].setText(f"{sizing['slew_torque_nm']*1000:.1f} mN·m")
        self._sc_labels["Slew momentum"].setText(f"{sizing['slew_momentum_nms']:.2f} N·m·s")
        self._sc_labels["Recommended wheel hmax"].setText(
            f"{sizing['recommended_wheel_hmax_nms']:.1f} N·m·s")

    def _run(self):
        name = self.sat_combo.currentText()
        if name:
            self.simulateRequested.emit(name)

    def current_satellite(self) -> str:
        return self.sat_combo.currentText()
