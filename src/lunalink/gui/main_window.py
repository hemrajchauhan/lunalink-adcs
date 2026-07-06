from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QSplitter, QVBoxLayout, QScrollArea,
)

from PyQt6.QtCore import Qt

from ..config import ( MAIN_WINDOW_WIDTH, MAIN_WINDOW_HEIGHT, SCENE_WIDTH,
                        CENTER_WIDTH, CONTROL_PANEL_HEIGHT, PLOT_PANEL_HEIGHT )

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

        # Two columns: the 3D scene on the left and the controls + plots on
        # the right (the plots get a large, draggable share of the height).
        # Mission details live inside the Mission tab.
        #
        # Both right-hand sections sit in scroll areas so the window and the
        # splitter can be resized freely: when a section becomes smaller than
        # its content, it scrolls instead of imposing a minimum window size.
        controls_scroll = QScrollArea()
        controls_scroll.setWidgetResizable(True)
        controls_scroll.setFrameShape(QScrollArea.Shape.NoFrame)
        controls_scroll.setWidget(self.control_panel)

        plots_scroll = QScrollArea()
        plots_scroll.setWidgetResizable(True)
        plots_scroll.setFrameShape(QScrollArea.Shape.NoFrame)
        plots_scroll.setWidget(self.plot_panel)

        right_splitter = QSplitter(Qt.Orientation.Vertical)
        right_splitter.addWidget(controls_scroll)
        right_splitter.addWidget(plots_scroll)
        right_splitter.setSizes([CONTROL_PANEL_HEIGHT, PLOT_PANEL_HEIGHT])
        right_splitter.setStretchFactor(1, 1)   # plots grow when the window does

        horizontal_splitter = QSplitter(Qt.Orientation.Horizontal)
        horizontal_splitter.addWidget(self.pyvista_view)
        horizontal_splitter.addWidget(right_splitter)
        horizontal_splitter.setSizes([SCENE_WIDTH, CENTER_WIDTH])

        main_layout.addWidget(horizontal_splitter)
