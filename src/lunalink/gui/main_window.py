from PyQt6.QtWidgets import QMainWindow, QWidget, QLabel, QSplitter, QVBoxLayout

from PyQt6.QtCore import Qt

from ..config import ( MAIN_WINDOW_WIDTH, MAIN_WINDOW_HEIGHT, LEFT_WINDOW_WIDTH, RIGHT_WINDOW_WIDTH, 
                        CONTROL_PANEL_HEIGHT, PLOT_PANEL_HEIGHT )

from .views.control_panel import ControlPanel
from .views.plot_panel import PlotPanel
from .views.pyvista_view import PyVistaView
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

        # Connect the ADCS control tab to the plot panel via the simulation.
        self.controller = SimulationController(
            self.control_panel.adcs_tab, self.plot_panel)

    def _create_layout(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        main_layout = QVBoxLayout()
        central_widget.setLayout(main_layout)

        # We need one horizontal splitter to separate the large 
        # PyVista area from the right-side panel, and a second vertical splitter
        # inside the right-side panel to separate the Control Panel from the Plot Area.

        horizontal_splitter = QSplitter(Qt.Orientation.Horizontal)
        horizontal_splitter.addWidget(self.pyvista_view)
        
        right_splitter = QSplitter(Qt.Orientation.Vertical)
        right_splitter.addWidget(self.control_panel)
        right_splitter.addWidget(self.plot_panel)
        right_splitter.setSizes([CONTROL_PANEL_HEIGHT, PLOT_PANEL_HEIGHT])

        horizontal_splitter.addWidget(right_splitter)
        horizontal_splitter.setSizes([LEFT_WINDOW_WIDTH, RIGHT_WINDOW_WIDTH])

        main_layout.addWidget(horizontal_splitter)
