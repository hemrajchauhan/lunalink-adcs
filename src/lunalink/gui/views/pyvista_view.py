from PyQt6.QtWidgets import QWidget, QVBoxLayout
from pyvistaqt import QtInteractor

from ..visualization.scene_manager import SceneManager


class PyVistaView(QWidget):

    def __init__(self, parent=None):
        super().__init__(parent)

        self._create_widgets()
        self._create_layout()

        # Kick off the orbital animation; the QTimer fires once the Qt event
        # loop is running.
        self.scene_manager.start_animation()

    def _create_widgets(self):
        self.plotter = QtInteractor(self)
        self.scene_manager = SceneManager(self.plotter)
        self.scene_manager.setup_scene()

    def _create_layout(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.plotter)
        self.setLayout(layout)

    def get_plotter(self):
        return self.plotter

    def get_scene_manager(self):
        return self.scene_manager
