from re import S
from tkinter import SE, SEL
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QTreeWidget, QTreeWidgetItem

from ....simulation.repositories.body_repository import BodyRepository
from ....simulation.repositories.satellite_repository import SatelliteRepository
from ....simulation.repositories import body_repository, satellite_repository

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

    def _create_layout(self):

        layout = QVBoxLayout()
        layout.addWidget(QLabel("Objects"))
        layout.addWidget(self.tree)

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