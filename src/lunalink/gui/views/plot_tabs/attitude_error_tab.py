import pyqtgraph as pg

from .base_plot_tab import BasePlotTab


class AttitudeErrorTab(BasePlotTab):

    TITLE = "Sun-pointing attitude error"
    LEFT_LABEL = ("Pointing error", "°")

    def update_plot(self, result):
        self.plot.plot(result["t_h"], result["attitude_error_deg"],
                       pen=pg.mkPen("#ffb347", width=2), name="pointing error")
