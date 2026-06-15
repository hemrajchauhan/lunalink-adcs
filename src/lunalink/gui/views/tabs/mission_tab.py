from PyQt6.QtWidgets import QWidget, QFormLayout, QLabel, QVBoxLayout, QGroupBox

from .... import config


class MissionTab(QWidget):
    """Read-only summary of the fixed mission parameters (from the brief)."""

    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        box = QGroupBox("Mission parameters (fixed)")
        form = QFormLayout(box)
        rows = [
            ("Orbit type", config.ORBIT_TYPE),
            ("Inclination", f"{config.INCLINATION}°  (critical inclination)"),
            ("Orbital period", f"≈ {config.ORBITAL_PERIOD} h"),
            ("Power budget (EOL)", f"{config.POWER_BUDGET_EOL} kW"),
            ("Design lifetime", f"≥ {config.DESIGN_LIFETIME} yr"),
            ("Earth downlink", config.EARTH_DOWNLINK),
            ("Moon uplink", config.MOON_UPLINK),
            ("Ground station", config.GROUND_STATION),
            ("Min. elevation", f"{config.MIN_ELEVATION}°"),
        ]
        for name, value in rows:
            form.addRow(QLabel(name), QLabel(str(value)))
        layout.addWidget(box)
        layout.addStretch()
