from PyQt6.QtWidgets  import QWidget, QVBoxLayout, QTabWidget

from .tabs.mission_tab import MissionTab
from .tabs.orbit_tab import OrbitTab
from .tabs.spacecraft_tab import SpacecraftTab
from .tabs.adcs_tab import ADCSTab
from .tabs.visualization_tab import VisualizationTab

class ControlPanel(QWidget):

    def __init__(self, parent=None):
        super().__init__(parent)

        self._create_widgets()
        self._create_layout()
        
    def _create_widgets(self):
        self.tab_widget = QTabWidget()

        self.mission_tab = MissionTab()
        self.orbit_tab = OrbitTab()
        self.spacecraft_tab = SpacecraftTab()
        self.adcs_tab = ADCSTab()
        self.visualization_tab = VisualizationTab()

    def _create_layout(self):
        self.tab_widget.addTab(self.mission_tab, "Mission")
        self.tab_widget.addTab(self.orbit_tab, "Orbit")
        self.tab_widget.addTab(self.spacecraft_tab, "Spacecraft")
        self.tab_widget.addTab(self.adcs_tab, "ADCS Control")
        self.tab_widget.addTab(self.visualization_tab, "Visualization")

        layout = QVBoxLayout()
        layout.addWidget(self.tab_widget)
        self.setLayout(layout)