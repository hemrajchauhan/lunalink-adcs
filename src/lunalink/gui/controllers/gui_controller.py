"""Wires the ADCS control tab to the simulation and the plot panel.

When the user runs a simulation (or shortly after startup), the controller
computes the ADCS time series on a background-friendly schedule and pushes the
result to every plot tab. A wait cursor is shown during the (few-second) run.
"""
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QGuiApplication

from ...simulation.adcs import simulate


class SimulationController:

    def __init__(self, adcs_tab, plot_panel):
        self.adcs_tab = adcs_tab
        self.plot_panel = plot_panel
        # The simulation runs only when the user asks (Run button / Mission tab),
        # not on startup. Plots show their "Run the simulation" hint until then.
        self.adcs_tab.parametersChanged.connect(self.run)

    def run(self, params):
        QGuiApplication.setOverrideCursor(Qt.CursorShape.WaitCursor)
        try:
            result = simulate(params)
            self.plot_panel.update_results(result)
        finally:
            QGuiApplication.restoreOverrideCursor()
