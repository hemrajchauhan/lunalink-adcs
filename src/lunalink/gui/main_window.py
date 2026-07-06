from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QSplitter, QVBoxLayout, QScrollArea, QPushButton,
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
        self._connect_results_visibility()

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
        # the right. Mission details live inside the Mission tab.
        #
        # Both right-hand sections sit in scroll areas so the window and the
        # splitter can be resized freely: when a section becomes smaller than
        # its content, it scrolls instead of imposing a minimum window size.
        controls_scroll = QScrollArea()
        controls_scroll.setWidgetResizable(True)
        controls_scroll.setFrameShape(QScrollArea.Shape.NoFrame)
        controls_scroll.setWidget(self.control_panel)

        self.plots_scroll = QScrollArea()
        self.plots_scroll.setWidgetResizable(True)
        self.plots_scroll.setFrameShape(QScrollArea.Shape.NoFrame)
        self.plots_scroll.setWidget(self.plot_panel)

        # The results area starts hidden: before the first simulation run the
        # plots are empty and would only take space away from the controls.
        # After the panel is closed with its X button, a slim bar allows
        # reopening it without re-running the simulation.
        self.show_results_button = QPushButton("Show simulation results")
        self.show_results_button.setToolTip(
            "Reopen the results panel with the plots of the last run.")

        self.results_area = QWidget()
        results_layout = QVBoxLayout(self.results_area)
        results_layout.setContentsMargins(0, 0, 0, 0)
        results_layout.setSpacing(0)
        results_layout.addWidget(self.show_results_button)
        results_layout.addWidget(self.plots_scroll)
        self.plots_scroll.hide()
        self.show_results_button.hide()
        # Hide the whole container until the first run: a hidden splitter
        # child receives no space, so the control panel gets the full column.
        self.results_area.hide()

        self.right_splitter = QSplitter(Qt.Orientation.Vertical)
        self.right_splitter.addWidget(controls_scroll)
        self.right_splitter.addWidget(self.results_area)
        self.right_splitter.setStretchFactor(1, 1)

        horizontal_splitter = QSplitter(Qt.Orientation.Horizontal)
        horizontal_splitter.addWidget(self.pyvista_view)
        horizontal_splitter.addWidget(self.right_splitter)
        horizontal_splitter.setSizes([SCENE_WIDTH, CENTER_WIDTH])

        main_layout.addWidget(horizontal_splitter)

    # -- results panel visibility -------------------------------------------
    def _connect_results_visibility(self):
        self.plot_panel.resultsUpdated.connect(self._show_results)
        self.plot_panel.closeRequested.connect(self._hide_results)
        self.show_results_button.clicked.connect(self._show_results)

    def _show_results(self):
        """Open the results panel (after a run, or via the reopen bar)."""
        self.show_results_button.hide()
        self.plots_scroll.show()
        self.results_area.show()
        self.right_splitter.setSizes([CONTROL_PANEL_HEIGHT, PLOT_PANEL_HEIGHT])

    def _hide_results(self):
        """Collapse the results panel to a slim reopen bar; the control
        panel takes over the freed space."""
        self.plots_scroll.hide()
        self.show_results_button.show()
        # Shrink the results slot to exactly the bar height so the control
        # panel is fully visible again.
        bar_height = self.show_results_button.sizeHint().height() + 4
        total = sum(self.right_splitter.sizes())
        self.right_splitter.setSizes([max(total - bar_height, 1), bar_height])
