"""Wires the ADCS control tab to the simulation and the plot panel.

When the user runs a simulation (or at startup), the controller computes the
ADCS time series and pushes the result to every plot tab.
"""
from ...simulation.adcs import simulate


class SimulationController:

    def __init__(self, adcs_tab, plot_panel):
        self.adcs_tab = adcs_tab
        self.plot_panel = plot_panel

        self.adcs_tab.parametersChanged.connect(self.run)
        # Render an initial result with the default parameters.
        self.run(self.adcs_tab.get_params())

    def run(self, params):
        result = simulate(params)
        self.plot_panel.update_results(result)
