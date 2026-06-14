from PyQt6.QtWidgets import QWidget, QVBoxLayout
from pyvistaqt import QtInteractor

from ..visualization.scene_manager import SceneManager

class PyVistaView(QWidget):

    def __init__(self, parent=None):
        super().__init__(parent)

        self._create_widgets()
        self._create_layout()

    def _create_widgets(self):
        self.plotter = QtInteractor(self)
        self.scene_manager = SceneManager(self.plotter)
        self.scene_manager.setup_scene()

    def _create_layout(self):
        layout = QVBoxLayout()
        layout.addWidget(self.plotter)
        self.setLayout(layout)

    def get_plotter(self):
        return self.plotter