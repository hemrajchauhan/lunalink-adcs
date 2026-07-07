"""Dialog for adding a celestial body or satellite.

Positions are NOT entered as raw XYZ. Instead the user picks a parent body and
describes the orbit relative to it (distance / altitude + a few orbital
elements); the dialog converts that into Keplerian elements and the simulation
computes the absolute position. This is far more intuitive than typing
heliocentric coordinates by hand.
"""
import numpy as np
from PyQt6.QtWidgets import (
    QDialog, QComboBox, QLineEdit, QDoubleSpinBox, QCheckBox, QPushButton,
    QFormLayout, QVBoxLayout, QHBoxLayout, QStackedWidget, QWidget, QLabel,
    QDialogButtonBox, QColorDialog, QMessageBox,
)
from PyQt6.QtGui import QColor

from ...config import AU_M
from ...simulation.objects import CelestialBody, Satellite, OrbitElements


def _spin(minimum, maximum, value, decimals=3, step=1.0, tip=""):
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


class AddObjectDialog(QDialog):

    def __init__(self, parent_body_names, parent=None, initial_type=None):
        super().__init__(parent)
        self.setWindowTitle("Add Object")
        self.setMinimumWidth(380)
        self._color = "#cccccc"
        self._parent_body_names = parent_body_names
        self._build_ui()
        if initial_type == "satellite":
            self.type_combo.setCurrentIndex(1)
        elif initial_type == "body":
            self.type_combo.setCurrentIndex(0)

    # ------------------------------------------------------------------
    def _build_ui(self):
        layout = QVBoxLayout(self)

        # Shared header: object type + name + colour.
        header = QFormLayout()
        self.type_combo = QComboBox()
        self.type_combo.addItems(["Celestial Body", "Satellite"])
        self.type_combo.currentIndexChanged.connect(self._on_type_changed)

        self.name_edit = QLineEdit()

        self.color_button = QPushButton("Pick colour…")
        self.color_button.clicked.connect(self._pick_color)
        self._update_color_button()

        self.type_combo.setToolTip("Add a planet or moon (Celestial Body) or a "
                                   "spacecraft (Satellite).")
        self.name_edit.setToolTip("A unique name for the new object.")
        self.color_button.setToolTip("Colour used to draw the object in the 3D view.")
        header.addRow(_labeled("Type", "Add a planet or moon (Celestial Body) or "
                               "a spacecraft (Satellite)."), self.type_combo)
        header.addRow(_labeled("Name", "A unique name for the new object."),
                      self.name_edit)
        header.addRow(_labeled("Colour", "Colour used to draw the object in the "
                               "3D view."), self.color_button)
        layout.addLayout(header)

        # Type-specific pages.
        self.stack = QStackedWidget()
        self.stack.addWidget(self._build_body_page())
        self.stack.addWidget(self._build_satellite_page())
        layout.addWidget(self.stack)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(self._on_accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def _build_body_page(self):
        page = QWidget()
        form = QFormLayout(page)

        self.body_radius = _spin(1, 2_000_000, 6371, decimals=1, step=100)
        self.body_tilt = _spin(0, 360, 23.4, decimals=2)
        self.body_rotation = _spin(-100000, 100000, 24, decimals=2)
        self.body_has_ring = QCheckBox("Has ring")

        # Physical environment used when a satellite orbits this body. Very large
        # / very small values (mass ~1e24, dipole ~1e15, density ~1e-12) are text
        # fields so scientific notation can be typed directly.
        self.body_mass = QLineEdit("5.97e24")
        self.body_mass.setToolTip("Mass of the body (kg). Sets its gravity "
                                  "(mu = G*mass), which drives the orbit and the "
                                  "gravity-gradient torque.")
        self.body_dipole = QLineEdit("0")
        self.body_dipole.setToolTip("Magnetic dipole strength (T*m^3); Earth is "
                                    "~7.94e15. Use 0 for a body with no global "
                                    "magnetic field (Moon, Mars).")
        self.body_atmos_rho = QLineEdit("0")
        self.body_atmos_rho.setToolTip("Reference atmospheric density (kg/m^3) at "
                                       "the reference altitude below. Use 0 for an "
                                       "airless body (no drag).")
        self.body_atmos_alt = _spin(0, 1e9, 0, decimals=0, step=1000,
                                    tip="Altitude (m) at which the reference "
                                        "density applies.")
        self.body_atmos_H = _spin(1, 1e7, 60000, decimals=0, step=1000,
                                  tip="Atmospheric scale height (m): the density "
                                      "falls by 1/e over this altitude change.")
        self.body_j2 = QLineEdit("0")
        self.body_j2.setToolTip("J2 oblateness coefficient (Earth ~1.08e-3). "
                                "Drives the reported orbit-plane drift; use 0 for "
                                "a perfect sphere.")

        self.body_parent = QComboBox()
        self.body_parent.addItem("(none, independent)")
        self.body_parent.addItems(self._parent_body_names)

        self.body_distance = _spin(0, 1000, 1.0, decimals=4, step=0.1)
        self.body_ecc = _spin(0, 0.99, 0.0, decimals=4, step=0.01)
        self.body_incl = _spin(0, 180, 0.0, decimals=2)
        self.body_raan = _spin(0, 360, 0.0, decimals=2)
        self.body_argp = _spin(0, 360, 0.0, decimals=2)
        self.body_anom = _spin(0, 360, 0.0, decimals=2)

        self.body_has_ring.setToolTip("Draw a Saturn-like ring around the body.")
        self.body_parent.setToolTip("The body this one orbits, or independent "
                                    "(orbits the Sun / scene origin).")
        _t = {
            "radius": "Physical radius of the body.",
            "tilt": "Tilt of the body's spin axis relative to its orbit plane.",
            "rot": "Time for one full rotation about its axis "
                   "(negative spins the other way).",
            "sma": "Average orbit radius around the parent, in astronomical "
                   "units (1 AU = Sun-Earth distance).",
            "ecc": "How stretched the orbit is (0 = circle, closer to 1 = very "
                   "elongated).",
            "incl": "Tilt of the orbit plane relative to the reference plane.",
            "raan": "Right ascension of the ascending node: swivels the orbit "
                    "plane around the vertical axis.",
            "argp": "Argument of periapsis: rotates the ellipse within its "
                    "orbit plane.",
            "anom": "Mean anomaly at epoch: where the body starts along its "
                    "orbit at time zero.",
        }
        for box, key in ((self.body_radius, "radius"), (self.body_tilt, "tilt"),
                         (self.body_rotation, "rot"), (self.body_distance, "sma"),
                         (self.body_ecc, "ecc"), (self.body_incl, "incl"),
                         (self.body_raan, "raan"), (self.body_argp, "argp"),
                         (self.body_anom, "anom")):
            box.setToolTip(_t[key])
        form.addRow(_labeled("Radius [km]", _t["radius"]), self.body_radius)
        form.addRow(_labeled("Axial tilt [°]", _t["tilt"]), self.body_tilt)
        form.addRow(_labeled("Rotation period [h]", _t["rot"]), self.body_rotation)
        form.addRow("", self.body_has_ring)
        form.addRow(QLabel("<b>Physical environment (for orbiting satellites)</b>"))
        form.addRow(_labeled("Mass [kg]", self.body_mass.toolTip()), self.body_mass)
        form.addRow(_labeled("Magnetic dipole [T·m³]", self.body_dipole.toolTip()),
                    self.body_dipole)
        form.addRow(_labeled("Atmosphere density [kg/m³]",
                    self.body_atmos_rho.toolTip()), self.body_atmos_rho)
        form.addRow(_labeled("Atmosphere ref altitude [m]",
                    self.body_atmos_alt.toolTip()), self.body_atmos_alt)
        form.addRow(_labeled("Atmosphere scale height [m]",
                    self.body_atmos_H.toolTip()), self.body_atmos_H)
        form.addRow(_labeled("J2 oblateness", self.body_j2.toolTip()), self.body_j2)
        form.addRow(QLabel("<b>Orbit (around parent)</b>"))
        form.addRow(_labeled("Parent", "The body this one orbits, or independent."),
                    self.body_parent)
        form.addRow(_labeled("Semi-major axis [AU]", _t["sma"]), self.body_distance)
        form.addRow(_labeled("Eccentricity", _t["ecc"]), self.body_ecc)
        form.addRow(_labeled("Inclination [°]", _t["incl"]), self.body_incl)
        form.addRow(_labeled("RAAN [°]", _t["raan"]), self.body_raan)
        form.addRow(_labeled("Arg. of periapsis [°]", _t["argp"]), self.body_argp)
        form.addRow(_labeled("Mean anomaly at epoch [°]", _t["anom"]), self.body_anom)
        return page

    def _build_satellite_page(self):
        page = QWidget()
        form = QFormLayout(page)

        self.sat_mass = _spin(0.1, 100000, 500, decimals=1, step=10)
        self.sat_length = _spin(0.01, 1000, 2.0, decimals=2)
        self.sat_width = _spin(0.01, 1000, 1.5, decimals=2)
        self.sat_height = _spin(0.01, 1000, 1.0, decimals=2)

        self.sat_parent = QComboBox()
        self.sat_parent.addItems(self._parent_body_names)
        # Prefer Earth as the default parent if present.
        if "Earth" in self._parent_body_names:
            self.sat_parent.setCurrentText("Earth")

        self.sat_perigee = _spin(0, 5_000_000, 500, decimals=1, step=50)
        self.sat_ecc = _spin(0, 0.99, 0.0, decimals=4, step=0.01)
        self.sat_incl = _spin(0, 180, 63.4, decimals=2)
        self.sat_raan = _spin(0, 360, 0.0, decimals=2)
        self.sat_argp = _spin(0, 360, 0.0, decimals=2)
        self.sat_anom = _spin(0, 360, 0.0, decimals=2)

        self.sat_parent.setToolTip("The body the spacecraft orbits.")
        _t = {
            "mass": "Total spacecraft mass.",
            "len": "Body size along its X axis.",
            "wid": "Body size along its Y axis.",
            "hei": "Body size along its Z axis.",
            "peri": "Height above the parent's surface at the closest point of "
                    "the orbit (perigee).",
            "ecc": "How stretched the orbit is (0 = circle, closer to 1 = very "
                   "elongated). A Molniya orbit uses about 0.72.",
            "incl": "Tilt of the orbit plane. 63.4° is the Molniya 'critical "
                    "inclination' that freezes the apogee over one hemisphere.",
            "raan": "Right ascension of the ascending node: swivels the orbit "
                    "plane around the vertical axis.",
            "argp": "Argument of periapsis: rotates the ellipse within its "
                    "orbit plane (270° puts apogee over the north).",
            "anom": "Mean anomaly at epoch: where the spacecraft starts along "
                    "its orbit at time zero.",
        }
        for box, key in ((self.sat_mass, "mass"), (self.sat_length, "len"),
                         (self.sat_width, "wid"), (self.sat_height, "hei"),
                         (self.sat_perigee, "peri"), (self.sat_ecc, "ecc"),
                         (self.sat_incl, "incl"), (self.sat_raan, "raan"),
                         (self.sat_argp, "argp"), (self.sat_anom, "anom")):
            box.setToolTip(_t[key])
        form.addRow(_labeled("Mass [kg]", _t["mass"]), self.sat_mass)
        form.addRow(_labeled("Length [m]", _t["len"]), self.sat_length)
        form.addRow(_labeled("Width [m]", _t["wid"]), self.sat_width)
        form.addRow(_labeled("Height [m]", _t["hei"]), self.sat_height)
        form.addRow(QLabel("<b>Orbit (around parent)</b>"))
        form.addRow(_labeled("Parent body", "The body the spacecraft orbits."),
                    self.sat_parent)
        form.addRow(_labeled("Perigee altitude [km]", _t["peri"]), self.sat_perigee)
        form.addRow(_labeled("Eccentricity", _t["ecc"]), self.sat_ecc)
        form.addRow(_labeled("Inclination [°]", _t["incl"]), self.sat_incl)
        form.addRow(_labeled("RAAN [°]", _t["raan"]), self.sat_raan)
        form.addRow(_labeled("Arg. of periapsis [°]", _t["argp"]), self.sat_argp)
        form.addRow(_labeled("Mean anomaly at epoch [°]", _t["anom"]), self.sat_anom)
        return page

    # ------------------------------------------------------------------
    def _on_type_changed(self, index):
        self.stack.setCurrentIndex(index)

    def _pick_color(self):
        color = QColorDialog.getColor(QColor(self._color), self, "Pick colour")
        if color.isValid():
            self._color = color.name()
            self._update_color_button()

    def _update_color_button(self):
        self.color_button.setText(self._color)
        self.color_button.setStyleSheet(
            f"background-color: {self._color}; color: "
            f"{'#000' if QColor(self._color).lightness() > 128 else '#fff'};")

    # ------------------------------------------------------------------
    def _on_accept(self):
        name = self.name_edit.text().strip()
        if not name:
            QMessageBox.warning(self, "Missing name", "Please enter a name.")
            return
        self.accept()

    def is_satellite(self) -> bool:
        return self.type_combo.currentIndex() == 1

    def build_object(self):
        """Return a populated CelestialBody or Satellite."""
        name = self.name_edit.text().strip()

        if self.is_satellite():
            parent = self.sat_parent.currentText()
            parent_radius = self._parent_radius_m(parent)
            e = self.sat_ecc.value()
            r_perigee = parent_radius + self.sat_perigee.value() * 1000.0
            a = r_perigee / (1 - e) if e < 1 else r_perigee
            orbit = OrbitElements(
                semi_major_axis_m=a, eccentricity=e,
                inclination_deg=self.sat_incl.value(),
                raan_deg=self.sat_raan.value(),
                arg_periapsis_deg=self.sat_argp.value(),
                mean_anomaly_epoch_deg=self.sat_anom.value(),
            )
            return Satellite(
                name=name, color=self._color, parent=parent, orbit=orbit,
                mass_kg=self.sat_mass.value(),
                dimensions_m=np.array([self.sat_length.value(),
                                       self.sat_width.value(),
                                       self.sat_height.value()]),
            )

        # Celestial body
        parent_text = self.body_parent.currentText()
        parent = None if parent_text.startswith("(none") else parent_text
        orbit = None
        if parent is not None:
            orbit = OrbitElements(
                semi_major_axis_m=self.body_distance.value() * AU_M,
                eccentricity=self.body_ecc.value(),
                inclination_deg=self.body_incl.value(),
                raan_deg=self.body_raan.value(),
                arg_periapsis_deg=self.body_argp.value(),
                mean_anomaly_epoch_deg=self.body_anom.value(),
            )
        def _f(edit, default=0.0):
            try:
                return float(edit.text())
            except (TypeError, ValueError):
                return default

        return CelestialBody(
            name=name, color=self._color, parent=parent, orbit=orbit,
            radius_m=self.body_radius.value() * 1000.0,
            axial_tilt_deg=self.body_tilt.value(),
            rotation_period_h=self.body_rotation.value(),
            has_ring=self.body_has_ring.isChecked(),
            mass_kg=_f(self.body_mass),
            magnetic_dipole_tm3=_f(self.body_dipole),
            atmosphere_ref_density_kg_m3=_f(self.body_atmos_rho),
            atmosphere_ref_altitude_m=self.body_atmos_alt.value(),
            atmosphere_scale_height_m=self.body_atmos_H.value(),
            j2=_f(self.body_j2),
        )

    def _parent_radius_m(self, parent_name):
        from ...simulation.repositories.body_repository import BodyRepository
        body = BodyRepository().get_by_name(parent_name)
        return body.radius_m if body else 6_378_137.0
