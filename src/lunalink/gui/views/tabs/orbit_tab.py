from PyQt6.QtWidgets import QWidget, QFormLayout, QLabel, QVBoxLayout, QGroupBox

from ....config import GM_EARTH
from ....simulation import orbits
from ....simulation.repositories.satellite_repository import SatelliteRepository

R_EARTH_M = 6.378e6


class OrbitTab(QWidget):
    """Derived orbital elements for the LunaLink spacecraft."""

    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        box = QGroupBox("LunaLink orbit (derived)")
        form = QFormLayout(box)

        sat = SatelliteRepository().get_by_name("LunaLink")
        if sat is not None and sat.orbit is not None:
            o = sat.orbit
            a = o.semi_major_axis_m
            e = o.eccentricity
            P = orbits.orbital_period_s(a, GM_EARTH)
            rows = [
                ("Semi-major axis a", f"{a/1000:,.0f} km"),
                ("Eccentricity e", f"{e:.4f}"),
                ("Perigee altitude", f"{(a*(1-e)-R_EARTH_M)/1000:,.0f} km"),
                ("Apogee altitude", f"{(a*(1+e)-R_EARTH_M)/1000:,.0f} km"),
                ("Inclination", f"{o.inclination_deg}°"),
                ("Arg. of perigee", f"{o.arg_periapsis_deg}°"),
                ("RAAN", f"{o.raan_deg}°"),
                ("Orbital period", f"{P/3600:.2f} h"),
            ]
            for name, value in rows:
                form.addRow(QLabel(name), QLabel(value))
            note = QLabel("Note: 500×36 000 km altitudes give P ≈ 10.7 h, not the\n"
                          "brief's ≈12 h. Altitudes kept (geometry-driven); see report.")
            note.setStyleSheet("color: #c9a227;")
            layout.addWidget(box)
            layout.addWidget(note)
        else:
            layout.addWidget(QLabel("LunaLink satellite not found."))
        layout.addStretch()
