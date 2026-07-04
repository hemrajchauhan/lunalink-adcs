import pyqtgraph as pg
from PyQt6.QtCore import Qt

from .base_plot_tab import BasePlotTab


class RWMomentumTab(BasePlotTab):

    TITLE = "Reaction-wheel stored momentum"
    LEFT_LABEL = ("Wheel momentum", "N·m·s")

    def update_plot(self, result):
        self.plot.plot(result["t_h"], result["wheel_momentum_mag_nms"],
                       pen=pg.mkPen("#46e0a0", width=2), name="|h_wheels|")

        # Per-wheel capacity and the desaturation trigger level, for context.
        capacity = result.get("rw_capacity_nms")
        if capacity is not None:
            self.plot.addItem(pg.InfiniteLine(
                pos=capacity, angle=0,
                pen=pg.mkPen("#e06c75", style=Qt.PenStyle.DashLine),
                label="per-wheel capacity",
                labelOpts={"color": "#e06c75", "position": 0.05}))
        trigger = result.get("desat_trigger_nms")
        if trigger is not None:
            self.plot.addItem(pg.InfiniteLine(
                pos=trigger, angle=0,
                pen=pg.mkPen("#c8a24a", style=Qt.PenStyle.DotLine),
                label="desaturation trigger",
                labelOpts={"color": "#c8a24a", "position": 0.35}))
