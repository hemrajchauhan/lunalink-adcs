from PyQt6.QtWidgets import (
    QMenu, QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QTreeWidget, QTreeWidgetItem, QFormLayout, QLineEdit, QMessageBox,
    QColorDialog,
)
from PyQt6.QtGui import QColor
from PyQt6.QtCore import Qt

from ....simulation.repositories.body_repository import BodyRepository
from ....simulation.repositories.satellite_repository import SatelliteRepository
from ...dialogs.add_object_dialog import AddObjectDialog


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

        self.add_button = QPushButton("Add…")
        self.add_button.clicked.connect(self._add_object)
        self.remove_button = QPushButton("Remove")
        self.remove_button.clicked.connect(self._remove_selected)

        self.save_button = QPushButton("Save changes")
        self.save_button.clicked.connect(self._save_object)

    def _create_layout(self):
        layout = QVBoxLayout()
        layout.addWidget(QLabel("Objects"))
        layout.addWidget(self.tree)

        self.property_layout = QFormLayout()
        layout.addLayout(self.property_layout)
        layout.addWidget(self.save_button)

        buttons = QHBoxLayout()
        buttons.addWidget(self.add_button)
        buttons.addWidget(self.remove_button)
        layout.addLayout(buttons)
        self.setLayout(layout)

    # ------------------------------------------------------------------
    def refresh(self):
        self.tree.clear()
        bodies = BodyRepository().load_all()
        satellites = SatelliteRepository().load_all()

        body_root = QTreeWidgetItem(["Celestial Bodies"])
        satellite_root = QTreeWidgetItem(["Satellites"])
        self.tree.addTopLevelItem(body_root)
        self.tree.addTopLevelItem(satellite_root)

        for body in bodies:
            body_root.addChild(QTreeWidgetItem([body.name]))
        for satellite in satellites:
            satellite_root.addChild(QTreeWidgetItem([satellite.name]))
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
            return  # unknown item, nothing to edit

        self.current_object_name = object_name
        self.original_object_name = object_name
        self._populate_property_editor(properties)

    def _populate_property_editor(self, properties):
        while self.property_layout.rowCount():
            self.property_layout.removeRow(0)
        self.property_fields.clear()

        for name, value in properties:
            field = QLineEdit(str(value))
            if name.lower() == "color":
                self.property_layout.addRow(QLabel(name), self._color_row(field))
            else:
                self.property_layout.addRow(QLabel(name), field)
            self.property_fields[name] = field

    def _color_row(self, field: QLineEdit) -> QWidget:
        container = QWidget()
        row = QHBoxLayout(container)
        row.setContentsMargins(0, 0, 0, 0)
        pick = QPushButton("Pick…")

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
            QMessageBox.critical(self, "Invalid value",
                                 f"Could not save changes:\n{error}")
            return

        self.refresh()
        self.scene_manager.reload_scene()

    # ------------------------------------------------------------------
    def _add_object(self):
        parent_names = [b.name for b in BodyRepository().load_all()]
        dialog = AddObjectDialog(parent_names, self)
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
            self.scene_manager.reload_scene()

    def _remove_selected(self):
        item = self.tree.currentItem()
        if item is None or item.text(0) in self.GROUP_LABELS:
            QMessageBox.information(self, "No selection",
                                    "Select an object to remove.")
            return
        self._delete_object(item)

    def _delete_object(self, item):
        object_name = item.text(0)
        confirm = QMessageBox.question(
            self, "Delete object", f"Delete '{object_name}'?")
        if confirm != QMessageBox.StandardButton.Yes:
            return

        if BodyRepository().get_by_name(object_name):
            BodyRepository().delete_body(object_name)
        elif SatelliteRepository().get_by_name(object_name):
            SatelliteRepository().delete_satellite(object_name)

        self.scene_manager.reload_scene()
        self.refresh()

    # ------------------------------------------------------------------
    def _focus_object(self, item, column):
        object_name = item.text(0)
        if object_name in self.GROUP_LABELS:
            return
        if BodyRepository().get_by_name(object_name):
            self.scene_manager.focus_on_body(object_name)
        elif SatelliteRepository().get_by_name(object_name):
            self.scene_manager.focus_on_satellite(object_name)

    def _show_context_menu(self, position):
        item = self.tree.itemAt(position)
        if item is None or item.text(0) in self.GROUP_LABELS:
            return
        menu = QMenu()
        focus_action = menu.addAction("Focus")
        delete_action = menu.addAction("Delete")
        selected = menu.exec(self.tree.viewport().mapToGlobal(position))
        if selected == focus_action:
            self._focus_object(item, 0)
        elif selected == delete_action:
            self._delete_object(item)
