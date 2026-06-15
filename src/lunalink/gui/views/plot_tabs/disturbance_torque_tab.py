import pyqtgraph as pg

from .base_plot_tab import BasePlotTab


class DisturbanceTorqueTab(BasePlotTab):

    TITLE = "Disturbance torque vs orbit position (peaks at perigee)"
    LEFT_LABEL = ("Disturbance torque", "N·m")

    def update_plot(self, result):
        self.plot.plot(result["t_h"], result["disturbance_nm"],
                       pen=pg.mkPen("#ff6b6b", width=2), name="|τ_dist|")
        self.plot.setLogMode(x=False, y=True)
