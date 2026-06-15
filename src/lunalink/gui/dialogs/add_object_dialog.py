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


def _spin(minimum, maximum, value, decimals=3, step=1.0, suffix=""):
    box = QDoubleSpinBox()
    box.setRange(minimum, maximum)
    box.setDecimals(decimals)
    box.setSingleStep(step)
    box.setValue(value)
    if suffix:
        box.setSuffix(suffix)
    return box


class AddObjectDialog(QDialog):

    def __init__(self, parent_body_names, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Add Object")
        self.setMinimumWidth(380)
        self._color = "#cccccc"
        self._parent_body_names = parent_body_names
        self._build_ui()

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

        header.addRow("Type", self.type_combo)
        header.addRow("Name", self.name_edit)
        header.addRow("Colour", self.color_button)
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

        self.body_radius = _spin(1, 2_000_000, 6371, decimals=1, step=100, suffix=" km")
        self.body_tilt = _spin(0, 360, 23.4, decimals=2, suffix=" °")
        self.body_rotation = _spin(-100000, 100000, 24, decimals=2, suffix=" h")
        self.body_has_ring = QCheckBox("Has ring")

        self.body_parent = QComboBox()
        self.body_parent.addItem("(none — independent)")
        self.body_parent.addItems(self._parent_body_names)

        self.body_distance = _spin(0, 1000, 1.0, decimals=4, step=0.1, suffix=" AU")
        self.body_ecc = _spin(0, 0.99, 0.0, decimals=4, step=0.01)
        self.body_incl = _spin(0, 180, 0.0, decimals=2, suffix=" °")
        self.body_raan = _spin(0, 360, 0.0, decimals=2, suffix=" °")
        self.body_argp = _spin(0, 360, 0.0, decimals=2, suffix=" °")
        self.body_anom = _spin(0, 360, 0.0, decimals=2, suffix=" °")

        form.addRow("Radius", self.body_radius)
        form.addRow("Axial tilt", self.body_tilt)
        form.addRow("Rotation period", self.body_rotation)
        form.addRow("", self.body_has_ring)
        form.addRow(QLabel("<b>Orbit (around parent)</b>"))
        form.addRow("Parent", self.body_parent)
        form.addRow("Distance / semi-major axis", self.body_distance)
        form.addRow("Eccentricity", self.body_ecc)
        form.addRow("Inclination", self.body_incl)
        form.addRow("RAAN", self.body_raan)
        form.addRow("Arg. of periapsis", self.body_argp)
        form.addRow("Mean anomaly @ epoch", self.body_anom)
        return page

    def _build_satellite_page(self):
        page = QWidget()
        form = QFormLayout(page)

        self.sat_mass = _spin(0.1, 100000, 500, decimals=1, step=10, suffix=" kg")
        self.sat_length = _spin(0.01, 1000, 2.0, decimals=2, suffix=" m")
        self.sat_width = _spin(0.01, 1000, 1.5, decimals=2, suffix=" m")
        self.sat_height = _spin(0.01, 1000, 1.0, decimals=2, suffix=" m")

        self.sat_parent = QComboBox()
        self.sat_parent.addItems(self._parent_body_names)
        # Prefer Earth as the default parent if present.
        if "Earth" in self._parent_body_names:
            self.sat_parent.setCurrentText("Earth")

        self.sat_perigee = _spin(0, 5_000_000, 500, decimals=1, step=50, suffix=" km")
        self.sat_ecc = _spin(0, 0.99, 0.0, decimals=4, step=0.01)
        self.sat_incl = _spin(0, 180, 63.4, decimals=2, suffix=" °")
        self.sat_raan = _spin(0, 360, 0.0, decimals=2, suffix=" °")
        self.sat_argp = _spin(0, 360, 0.0, decimals=2, suffix=" °")
        self.sat_anom = _spin(0, 360, 0.0, decimals=2, suffix=" °")

        form.addRow("Mass", self.sat_mass)
        form.addRow("Length", self.sat_length)
        form.addRow("Width", self.sat_width)
        form.addRow("Height", self.sat_height)
        form.addRow(QLabel("<b>Orbit (around parent)</b>"))
        form.addRow("Parent body", self.sat_parent)
        form.addRow("Perigee altitude", self.sat_perigee)
        form.addRow("Eccentricity", self.sat_ecc)
        form.addRow("Inclination", self.sat_incl)
        form.addRow("RAAN", self.sat_raan)
        form.addRow("Arg. of periapsis", self.sat_argp)
        form.addRow("Mean anomaly @ epoch", self.sat_anom)
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
        return CelestialBody(
            name=name, color=self._color, parent=parent, orbit=orbit,
            radius_m=self.body_radius.value() * 1000.0,
            axial_tilt_deg=self.body_tilt.value(),
            rotation_period_h=self.body_rotation.value(),
            has_ring=self.body_has_ring.isChecked(),
        )

    def _parent_radius_m(self, parent_name):
        from ...simulation.repositories.body_repository import BodyRepository
        body = BodyRepository().get_by_name(parent_name)
        return body.radius_m if body else 6_378_137.0
