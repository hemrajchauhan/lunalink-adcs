"""Wires the ADCS control tab to the simulation, the plot panel and the
3D scene.

When the user runs a simulation, the controller computes the ADCS time
series, pushes the result to every plot tab, and hands the attitude history
to the 3D scene so the satellite mesh visibly rotates with the simulated
attitude. A wait cursor is shown during the (few-second) run.
"""
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QGuiApplication

from ...simulation.simulator import simulate


class SimulationController:

    def __init__(self, adcs_tab, plot_panel, scene_manager=None):
        self.adcs_tab = adcs_tab
        self.plot_panel = plot_panel
        self.scene_manager = scene_manager
        # The simulation runs only when the user asks (Run button / Mission tab),
        # not on startup. Plots show their "Run the simulation" hint until then.
        self.adcs_tab.parametersChanged.connect(self.run)

    def run(self, params):
        QGuiApplication.setOverrideCursor(Qt.CursorShape.WaitCursor)
        try:
            result = simulate(params)
            self.plot_panel.update_results(result)
            self._animate_attitude(result)
            if hasattr(self.adcs_tab, "show_run_summary"):
                self.adcs_tab.show_run_summary(result)
        except Exception as exc:                      # surface, don't crash the GUI
            if hasattr(self.adcs_tab, "show_run_error"):
                self.adcs_tab.show_run_error(str(exc))
            else:
                raise
        finally:
            QGuiApplication.restoreOverrideCursor()

    def _animate_attitude(self, result):
        """Attach the simulated attitude to the satellite in the 3D scene."""
        if self.scene_manager is None:
            return
        name = getattr(self.adcs_tab, "current_satellite_name", None)
        if not name or "quaternion" not in result:
            return
        try:
            self.scene_manager.set_attitude_history(
                name, result["t_h"] * 3600.0, result["quaternion"])
        except Exception:
            # The 3D view is optional; never let it break a simulation run.
            pass
