"""Wires the ADCS control tab to the simulation, the plot panel and the
3D scene.

When the user runs a simulation the work is done on a background thread so the
GUI never freezes. As soon as the (few-second) run finishes, the controller
pushes the result to every plot tab and hands the attitude history to the 3D
scene, which then plays the orientation back from the start at the current
playback speed so the behaviour is visible in real time.
"""
from PyQt6.QtCore import QObject, QThread, pyqtSignal

from ...simulation.simulator import simulate


class _SimWorker(QObject):
    """Runs one simulation off the GUI thread and reports the outcome."""

    finished = pyqtSignal(object)
    failed = pyqtSignal(str)

    def __init__(self, params):
        super().__init__()
        self._params = params

    def run(self):
        try:
            result = simulate(self._params)
        except Exception as exc:                       # report, don't crash
            self.failed.emit(str(exc))
        else:
            self.finished.emit(result)


class SimulationController:

    def __init__(self, adcs_tab, plot_panel, scene_manager=None):
        self.adcs_tab = adcs_tab
        self.plot_panel = plot_panel
        self.scene_manager = scene_manager
        self._thread = None
        self._worker = None
        # The simulation runs only when the user asks (Run button / Mission tab),
        # not on startup. Plots show their "Run the simulation" hint until then.
        self.adcs_tab.parametersChanged.connect(self.run)

    def run(self, params):
        # Never block the GUI: compute on a worker thread. Ignore a new request
        # while one is still running (the sim only takes a few seconds).
        if self._thread is not None and self._thread.isRunning():
            return
        self._thread = QThread()
        self._worker = _SimWorker(params)
        self._worker.moveToThread(self._thread)
        self._thread.started.connect(self._worker.run)
        self._worker.finished.connect(self._on_finished)
        self._worker.failed.connect(self._on_failed)
        self._worker.finished.connect(self._thread.quit)
        self._worker.failed.connect(self._thread.quit)
        self._thread.finished.connect(self._cleanup)
        self._thread.start()

    def _on_finished(self, result):
        self.plot_panel.update_results(result)
        self._animate_attitude(result)
        if hasattr(self.adcs_tab, "show_run_summary"):
            self.adcs_tab.show_run_summary(result)

    def _on_failed(self, message):
        if hasattr(self.adcs_tab, "show_run_error"):
            self.adcs_tab.show_run_error(message)

    def _cleanup(self):
        if self._worker is not None:
            self._worker.deleteLater()
        if self._thread is not None:
            self._thread.deleteLater()
        self._worker = None
        self._thread = None

    def _animate_attitude(self, result):
        """Attach the simulated attitude to the satellite and play it back."""
        if self.scene_manager is None:
            return
        name = getattr(self.adcs_tab, "current_satellite_name", None)
        if not name or "quaternion" not in result:
            return
        try:
            self.scene_manager.set_attitude_history(
                name, result["t_h"] * 3600.0, result["quaternion"])
            # Rewind the 3D clock and play the orientation from the beginning.
            self.scene_manager.play_attitude(name)
        except Exception:
            # The 3D view is optional; never let it break a simulation run.
            pass
