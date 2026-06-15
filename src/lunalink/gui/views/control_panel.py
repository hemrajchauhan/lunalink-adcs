from PyQt6.QtWidgets import QWidget, QVBoxLayout, QTabWidget

from .tabs.mission_tab import MissionTab
from .tabs.adcs_tab import ADCSTab
from .tabs.visualization_tab import VisualizationTab
from .tabs.objects_tab import ObjectsTab


class ControlPanel(QWidget):

    def __init__(self, scene_manager, parent=None):
        super().__init__(parent)
        self.scene_manager = scene_manager
        self._create_widgets()
        self._create_layout()
        self._connect()

    def _create_widgets(self):
        self.tab_widget = QTabWidget()
        self.mission_tab = MissionTab()
        self.adcs_tab = ADCSTab()
        self.visualization_tab = VisualizationTab(self.scene_manager)
        self.objects_tab = ObjectsTab(self.scene_manager)

    def _create_layout(self):
        self.tab_widget.addTab(self.mission_tab, "Mission")
        self.tab_widget.addTab(self.adcs_tab, "ADCS Simulation")
        self.tab_widget.addTab(self.visualization_tab, "Visualization")
        self.tab_widget.addTab(self.objects_tab, "Objects")
        layout = QVBoxLayout()
        layout.addWidget(self.tab_widget)
        self.setLayout(layout)

    def _connect(self):
        # "Run" on the Mission tab drives the ADCS simulation for that satellite.
        self.mission_tab.simulateRequested.connect(self._run_for_satellite)

    def _run_for_satellite(self, name):
        self.adcs_tab.select_satellite(name)
        self.adcs_tab.run_now()
        self.tab_widget.setCurrentWidget(self.adcs_tab)
