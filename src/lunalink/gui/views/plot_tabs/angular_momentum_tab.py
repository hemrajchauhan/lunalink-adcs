import pyqtgraph as pg

from .base_plot_tab import BasePlotTab


class AngularMomentumTab(BasePlotTab):
    """Total |H| = |I omega + h_w| - integrator sanity check (framework 5.3)."""

    TITLE = "Total angular momentum |H| (integrator check)"
    LEFT_LABEL = ("|H|", "N·m·s")

    def update_plot(self, result):
        self.plot.plot(result["t_h"], result["angular_momentum_nms"],
                       pen=pg.mkPen("#b388ff", width=2), name="|H|")
