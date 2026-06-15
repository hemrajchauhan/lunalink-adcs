import pyqtgraph as pg

from .base_plot_tab import BasePlotTab


class RWMomentumTab(BasePlotTab):

    TITLE = "Reaction-wheel stored momentum (desaturation saw-tooth)"
    LEFT_LABEL = ("Wheel momentum", "N·m·s")

    def update_plot(self, result):
        self.plot.plot(result["t_h"], result["wheel_momentum_mag_nms"],
                       pen=pg.mkPen("#46e0a0", width=2), name="|h_wheels|")
