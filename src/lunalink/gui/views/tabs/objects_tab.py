from PyQt6.QtWidgets import ( QMenu, QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, 
                             QTreeWidget, QTreeWidgetItem, QFormLayout, QLineEdit )
from PyQt6.QtCore import Qt
import numpy as np

from ....simulation.repositories.body_repository import BodyRepository
from ....simulation.repositories.satellite_repository import SatelliteRepository
from ....simulation.objects import CelestialBody, Satellite

class ObjectsTab(QWidget):

    def __init__(self, scene_manager, parent=None):
        super().__init__(parent)
        
        self.scene_manager = scene_manager

        self._create_widgets()
        self._create_layout()
        self.refresh()

    def _create_widgets(self):

        self.tree = QTreeWidget()
        self.tree.setHeaderLabel("Mission Objects")
        self.add_button = QPushButton("Add")
        self.remove_button = QPushButton("Remove")
        
        self.tree.itemDoubleClicked.connect(self._focus_object)
        self.tree.itemClicked.connect(self._load_properties)
        self.tree.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.tree.customContextMenuRequested.connect(self._show_context_menu)

        self.property_fields = {}

        self.save_button = QPushButton("Save")
        self.save_button.clicked.connect(self._save_object)

        self.current_object_name = None
        self.current_object_type = None


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

    def refresh(self):

        self.tree.clear()

        body_repository = BodyRepository()
        satellite_repository = SatelliteRepository()
        
        bodies = body_repository.load_all()
        satellites = satellite_repository.load_all()

        body_root = QTreeWidgetItem(["Celestial Bodies"])
        satellite_root = QTreeWidgetItem(["Satellites"])

        self.tree.addTopLevelItem(body_root)
        self.tree.addTopLevelItem(satellite_root)

        for body in bodies:
            body_root.addChild(QTreeWidgetItem([body.name]))

        for satellite in satellites:
            satellite_root.addChild(QTreeWidgetItem([satellite.name]))

        self.tree.expandAll()

    def _load_properties(self, item, column):
        object_name = item.text(0)
        if object_name in ("Celestial Bodies", "Satellites"):
            return

        self.current_object_name = object_name
        self.original_object_name = object_name
        body_repository = BodyRepository()
        satellite_repository = SatelliteRepository()

        body = body_repository.get_by_name(object_name)
        satellite = satellite_repository.get_by_name(object_name)
        if body:
            self.current_object_type = "body"
            properties = body_repository.get_properties(object_name)
        elif satellite:
            self.current_object_type = "satellite"
            properties = satellite_repository.get_properties(object_name)

        self._populate_property_editor(properties)
      
    def _populate_property_editor(self, properties):
        while self.property_layout.rowCount():
            self.property_layout.removeRow(0)
        self.property_fields.clear()

        for name, value in properties:
            field = QLineEdit()
            field.setText(str(value))
            self.property_layout.addRow(QLabel(name), field)
            self.property_fields[name] = field

    def _save_object(self):
        if self.current_object_name is None:
            return

        properties = {}
        for name, field in self.property_fields.items():
            properties[name] = field.text()

        if self.current_object_type == "body":
            BodyRepository().save_properties(self.original_object_name, properties)
        elif self.current_object_type == "satellite":
            SatelliteRepository().save_properties(self.original_object_name, properties)

        self.refresh()
        self.scene_manager.reload_scene()

    def _focus_object(self, item, column):

        object_name = item.text(0)
        body_repository = BodyRepository()
        satellite_repository = SatelliteRepository()

        body_names = [body.name for body in body_repository.load_all()]
        satellite_names = [satellite.name for satellite in satellite_repository.load_all()]

        if object_name in body_names:
            self.scene_manager.focus_on_body(object_name)

        elif object_name in satellite_names:
            self.scene_manager.focus_on_satellite(object_name)

    def _show_context_menu(self, position):
        item = self.tree.itemAt(position)
        if item is None:
            return
        
        object_name = item.text(0)
        if object_name in ("Celestial Bodies", "Satellites"):
            return

        menu = QMenu()
        
        focus_action = menu.addAction("Focus")
        delete_action = menu.addAction("Delete")
        selected_action = menu.exec(self.tree.viewport().mapToGlobal(position))
        
        if selected_action == focus_action:
            self._focus_object(item, 0)
        elif selected_action == delete_action:
            self._delete_object(item)

    def _delete_object(self, item):
        object_name = item.text(0)
        body_repository = BodyRepository()
        satellite_repository = SatelliteRepository()
        
        if body_repository.get_by_name(object_name):
            body_repository.delete_body(object_name)
        elif satellite_repository.get_by_name(object_name):
            satellite_repository.delete_satellite(object_name)

        self.scene_manager.reload_scene()
        self.refresh()