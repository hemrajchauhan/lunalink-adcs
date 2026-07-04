from PyQt6.QtWidgets import QMainWindow, QWidget, QLabel, QSplitter, QVBoxLayout

from PyQt6.QtCore import Qt

from ..config import ( MAIN_WINDOW_WIDTH, MAIN_WINDOW_HEIGHT, SCENE_WIDTH, CENTER_WIDTH,
                        MISSION_INFO_WIDTH, CONTROL_PANEL_HEIGHT, PLOT_PANEL_HEIGHT )

from .views.control_panel import ControlPanel
from .views.plot_panel import PlotPanel
from .views.pyvista_view import PyVistaView
from .views.mission_info_panel import MissionInfoPanel
from .controllers.gui_controller import SimulationController

class MainWindow(QMainWindow):

    def __init__(self):
        super().__init__()

        self.setWindowTitle("LunaLink ADCS Simulator")
        self.resize(MAIN_WINDOW_WIDTH, MAIN_WINDOW_HEIGHT)

        self._create_widgets()
        self._create_layout()

    def _create_widgets(self):
        self.pyvista_view = PyVistaView()
        self.scene_manager = self.pyvista_view.get_scene_manager()
        self.control_panel = ControlPanel(self.scene_manager)
        self.plot_panel = PlotPanel()
        self.mission_info_panel = MissionInfoPanel()

        # Connect the ADCS control tab to the plot panel via the simulation.
        self.controller = SimulationController(
            self.control_panel.adcs_tab, self.plot_panel)

        # The read-only Mission Details panel follows the Mission tab selection.
        mission_tab = self.control_panel.mission_tab
        mission_tab.missionChanged.connect(self.mission_info_panel.update_for_mission)
        self.mission_info_panel.update_for_mission(mission_tab.current_mission())

    def _create_layout(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        main_layout = QVBoxLayout()
        central_widget.setLayout(main_layout)

        # Three columns: read-only Mission Details on the left, the 3D scene
        # (planets) in the centre, and the controls + plots on the right (the
        # plots get a large, draggable share of the height).
        right_splitter = QSplitter(Qt.Orientation.Vertical)
        right_splitter.addWidget(self.control_panel)
        right_splitter.addWidget(self.plot_panel)
        right_splitter.setSizes([CONTROL_PANEL_HEIGHT, PLOT_PANEL_HEIGHT])
        right_splitter.setStretchFactor(1, 1)   # plots grow when the window does

        horizontal_splitter = QSplitter(Qt.Orientation.Horizontal)
        horizontal_splitter.addWidget(self.mission_info_panel)
        horizontal_splitter.addWidget(self.pyvista_view)
        horizontal_splitter.addWidget(right_splitter)
        horizontal_splitter.setSizes([MISSION_INFO_WIDTH, SCENE_WIDTH, CENTER_WIDTH])

        main_layout.addWidget(horizontal_splitter)
