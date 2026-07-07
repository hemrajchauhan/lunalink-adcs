from PyQt6.QtWidgets import (
    QMenu, QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QTreeWidget, QTreeWidgetItem, QFormLayout, QLineEdit, QMessageBox,
    QColorDialog, QScrollArea, QSizePolicy,
)
from PyQt6.QtGui import QColor
from PyQt6.QtCore import Qt

from ....simulation.repositories.body_repository import BodyRepository
from ....simulation.repositories.satellite_repository import SatelliteRepository
from ...dialogs.add_object_dialog import AddObjectDialog

# Hover explanations for the editable object properties (shown on the label and
# the field). Keys match the names returned by the repositories.
_PROPERTY_TIPS = {
    "Name": "The object's unique name.",
    "Color": "Colour used to draw the object in the 3D view (e.g. #4488ff).",
    "Radius (m)": "Physical radius of the body, in metres.",
    "Axial tilt (deg)": "Tilt of the body's spin axis relative to its orbit plane.",
    "Rotation period (h)": "Time for one full rotation about its axis "
                           "(negative spins the other way).",
    "Has ring": "Whether a Saturn-like ring is drawn (true/false).",
    "Parent": "The body this object orbits.",
    "Mass (kg)": "Mass of the object. For a central body it sets the gravity "
                 "(mu = G*mass) felt by satellites orbiting it.",
    "Magnetic dipole (T m^3)": "Strength of the body's magnetic dipole field "
                               "(Earth ~7.94e15). 0 = no global field, so no "
                               "magnetic torque on satellites.",
    "Atmosphere density (kg/m^3)": "Reference atmospheric density at the reference "
                                   "altitude. 0 = airless (no drag).",
    "Atmosphere ref altitude (m)": "Altitude at which the reference density "
                                   "applies.",
    "Atmosphere scale height (m)": "Altitude change over which the density falls "
                                   "by a factor of 1/e.",
    "J2 oblateness": "Oblateness coefficient (Earth ~1.08e-3). Drives the reported "
                     "orbit-plane drift rates; 0 for a perfect sphere.",
    "Length (m)": "Body size along its X axis.",
    "Width (m)": "Body size along its Y axis.",
    "Height (m)": "Body size along its Z axis.",
    "Distance to parent (m)": "Semi-major axis of the orbit around the parent.",
    "Semi-major axis (m)": "Average orbit radius (half the ellipse's long axis).",
    "Eccentricity": "How stretched the orbit is (0 = circle, closer to 1 = "
                    "very elongated).",
    "Inclination (deg)": "Tilt of the orbit plane relative to the reference plane.",
    "RAAN (deg)": "Right ascension of the ascending node: swivels the orbit "
                  "plane around the vertical axis.",
    "Arg periapsis (deg)": "Argument of periapsis: rotates the ellipse within "
                           "its orbit plane.",
    "Mean anomaly (deg)": "Starting position of the object along its orbit at "
                          "time zero.",
}


class ObjectsTab(QWidget):

    GROUP_LABELS = ("Celestial Bodies", "Satellites")

    def __init__(self, scene_manager, parent=None):
        super().__init__(parent)
        self.scene_manager = scene_manager
        self.property_fields = {}
        self.current_object_name = None
        self.original_object_name = None
        self.current_object_type = None

        self._create_widgets()
        self._create_layout()
        self.refresh()

    def _create_widgets(self):
        self.tree = QTreeWidget()
        self.tree.setHeaderLabel("Mission Objects")
        self.tree.itemDoubleClicked.connect(self._focus_object)
        self.tree.itemClicked.connect(self._load_properties)
        self.tree.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.tree.customContextMenuRequested.connect(self._show_context_menu)

        self.save_button = QPushButton("Save changes")
        self.save_button.clicked.connect(self._save_object)

    def _create_layout(self):
        layout = QVBoxLayout()
        hint = QLabel("Right-click to add or remove an object. "
                      "Double-click an object to centre the camera on it.")
        hint.setWordWrap(True)
        layout.addWidget(hint)
        # The tree gets the lion's share of the space.
        layout.addWidget(self.tree, stretch=3)

        # Compact, scrollable property editor so it never hides the tree.
        self.editor_label = QLabel("Properties")
        layout.addWidget(self.editor_label)

        self.property_container = QWidget()
        self.property_layout = QFormLayout(self.property_container)
        self.property_layout.setContentsMargins(4, 4, 4, 4)

        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setWidget(self.property_container)
        self.scroll.setMaximumHeight(220)
        self.scroll.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed)
        layout.addWidget(self.scroll, stretch=1)
        layout.addWidget(self.save_button)
        self.setLayout(layout)

    # ------------------------------------------------------------------
    def refresh(self):
        self.tree.clear()
        bodies = BodyRepository().load_all()
        satellites = SatelliteRepository().load_all()
        self.body_root = QTreeWidgetItem(["Celestial Bodies"])
        self.satellite_root = QTreeWidgetItem(["Satellites"])
        self.tree.addTopLevelItem(self.body_root)
        self.tree.addTopLevelItem(self.satellite_root)
        for body in bodies:
            self.body_root.addChild(QTreeWidgetItem([body.name]))
        for satellite in satellites:
            self.satellite_root.addChild(QTreeWidgetItem([satellite.name]))
        self.tree.expandAll()

    # ------------------------------------------------------------------
    def _load_properties(self, item, column):
        object_name = item.text(0)
        if object_name in self.GROUP_LABELS:
            return
        body = BodyRepository().get_by_name(object_name)
        satellite = SatelliteRepository().get_by_name(object_name)
        if body is not None:
            self.current_object_type = "body"
            properties = BodyRepository().get_properties(object_name)
        elif satellite is not None:
            self.current_object_type = "satellite"
            properties = SatelliteRepository().get_properties(object_name)
        else:
            return
        self.current_object_name = object_name
        self.original_object_name = object_name
        self.editor_label.setText(f"Properties: {object_name}")
        self._populate_property_editor(properties)

    def _populate_property_editor(self, properties):
        while self.property_layout.rowCount():
            self.property_layout.removeRow(0)
        self.property_fields.clear()
        for name, value in properties:
            field = QLineEdit(str(value))
            tip = _PROPERTY_TIPS.get(name, "")
            if tip:
                field.setToolTip(tip)
            label = QLabel(name)
            if tip:
                label.setToolTip(tip)
            if name.lower() == "color":
                self.property_layout.addRow(label, self._color_row(field))
            else:
                self.property_layout.addRow(label, field)
            self.property_fields[name] = field

    def _color_row(self, field: QLineEdit) -> QWidget:
        container = QWidget()
        row = QHBoxLayout(container)
        row.setContentsMargins(0, 0, 0, 0)
        pick = QPushButton("Pick…")
        pick.setMaximumWidth(60)

        def choose():
            color = QColorDialog.getColor(QColor(field.text() or "#ffffff"), self)
            if color.isValid():
                field.setText(color.name())

        pick.clicked.connect(choose)
        row.addWidget(field)
        row.addWidget(pick)
        return container

    def _save_object(self):
        if self.current_object_name is None:
            QMessageBox.information(self, "No selection",
                                    "Select an object in the tree first.")
            return
        properties = {name: field.text() for name, field in self.property_fields.items()}
        try:
            if self.current_object_type == "body":
                BodyRepository().save_properties(self.original_object_name, properties)
            elif self.current_object_type == "satellite":
                SatelliteRepository().save_properties(self.original_object_name, properties)
        except (ValueError, KeyError) as error:
            QMessageBox.critical(self, "Invalid value", f"Could not save changes:\n{error}")
            return
        self.refresh()
        self._reload_scene_safe()

    # ------------------------------------------------------------------
    def _add_object(self, initial_type=None):
        parent_names = [b.name for b in BodyRepository().load_all()]
        dialog = AddObjectDialog(parent_names, self, initial_type=initial_type)
        if dialog.exec():
            obj = dialog.build_object()
            try:
                if dialog.is_satellite():
                    SatelliteRepository().add_satellite(obj)
                else:
                    BodyRepository().add_body(obj)
            except (ValueError, KeyError) as error:
                QMessageBox.critical(self, "Could not add object", str(error))
                return
            self.refresh()
            self._reload_scene_safe()

    def _delete_object(self, item):
        object_name = item.text(0)
        if QMessageBox.question(self, "Delete object", f"Delete '{object_name}'?") \
                != QMessageBox.StandardButton.Yes:
            return
        if BodyRepository().get_by_name(object_name):
            BodyRepository().delete_body(object_name)
        elif SatelliteRepository().get_by_name(object_name):
            SatelliteRepository().delete_satellite(object_name)

        # Clear the editor if the deleted object was being shown.
        if self.current_object_name == object_name:
            self.current_object_name = None
            self.original_object_name = None
            self.current_object_type = None
            self.editor_label.setText("Properties")
            self._populate_property_editor([])

        # Rebuild the tree first (so it always reflects the deletion), then
        # refresh the 3D scene (guarded so a scene hiccup can't leave the
        # tree stale).
        self.refresh()
        self._reload_scene_safe()

    def _reload_scene_safe(self):
        try:
            self.scene_manager.reload_scene()
        except Exception as error:
            QMessageBox.warning(self, "Scene refresh",
                                f"Saved; the 3D view could not refresh:\n{error}")

    def _focus_object(self, item, column=0):
        object_name = item.text(0)
        if object_name in self.GROUP_LABELS:
            return
        if BodyRepository().get_by_name(object_name):
            self.scene_manager.focus_on_body(object_name)
        elif SatelliteRepository().get_by_name(object_name):
            self.scene_manager.focus_on_satellite(object_name)

    def _show_context_menu(self, position):
        item = self.tree.itemAt(position)
        menu = QMenu()
        label = item.text(0) if item is not None else None

        if label == "Satellites":
            menu.addAction("Add Satellite…", lambda: self._add_object("satellite"))
        elif label == "Celestial Bodies":
            menu.addAction("Add Celestial Body…", lambda: self._add_object("body"))
        elif item is None:
            menu.addAction("Add Celestial Body…", lambda: self._add_object("body"))
            menu.addAction("Add Satellite…", lambda: self._add_object("satellite"))
        else:
            # An actual object: focus / add / remove.
            menu.addAction("Focus", lambda: self._focus_object(item))
            menu.addSeparator()
            menu.addAction("Add Celestial Body…", lambda: self._add_object("body"))
            menu.addAction("Add Satellite…", lambda: self._add_object("satellite"))
            menu.addSeparator()
            menu.addAction("Remove", lambda: self._delete_object(item))

        menu.exec(self.tree.viewport().mapToGlobal(position))
