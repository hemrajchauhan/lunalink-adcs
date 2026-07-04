import pyqtgraph as pg
from PyQt6.QtCore import Qt

from .base_plot_tab import BasePlotTab

_TITLES = {
    "slew": "Slew attitude error (angle to commanded attitude)",
    "detumble": "Attitude error vs the Sun line (uncontrolled during detumble)",
    "full": "Attitude error — detumble, then Sun acquisition and hold",
}


class AttitudeErrorTab(BasePlotTab):

    TITLE = "Sun-pointing attitude error"
    LEFT_LABEL = ("Pointing error", "°")

    def update_plot(self, result):
        self.plot.setTitle(_TITLES.get(result.get("mode"), self.TITLE),
                           color="#e6e6e6", size="11pt")
        self.plot.plot(result["t_h"], result["attitude_error_deg"],
                       pen=pg.mkPen("#ffb347", width=2), name="pointing error")

        # "Acquired" threshold and the moment it was first met.
        threshold = result.get("acquire_threshold_deg")
        if threshold is not None:
            self.plot.addItem(pg.InfiniteLine(
                pos=threshold, angle=0,
                pen=pg.mkPen("#6fae6f", style=Qt.PenStyle.DashLine),
                label=f"acquired < {threshold:g}°",
                labelOpts={"color": "#6fae6f", "position": 0.05}))
        acquire = result.get("t_acquire_h")
        if acquire is not None:
            self.plot.addItem(pg.InfiniteLine(
                pos=acquire, angle=90,
                pen=pg.mkPen("#aaaa55", style=Qt.PenStyle.DashLine)))
