import pyqtgraph as pg
from PyQt6.QtCore import Qt

from .base_plot_tab import BasePlotTab


class AngularVelocityTab(BasePlotTab):

    TITLE = "Body angular velocity"
    LEFT_LABEL = ("Angular velocity", "°/s")

    _TITLES = {
        "detumble": "Body angular velocity — detumbling convergence",
        "full": "Body angular velocity — detumble, then pointing",
        "slew": "Body angular velocity — slew rate profile",
        "sun_pointing": "Body angular velocity — rate damping while pointing",
    }

    def update_plot(self, result):
        self.plot.setTitle(self._TITLES.get(result.get("mode"), self.TITLE),
                           color="#e6e6e6", size="11pt")
        t = result["t_h"]
        omega = result["omega_deg_s"]
        colors = ("#ff6b6b", "#5cd65c", "#5b9bff")
        for i, c in enumerate(colors):
            self.plot.plot(t, omega[:, i], pen=pg.mkPen(c, width=1.4),
                           name=f"ω{['x', 'y', 'z'][i]}")
        self.plot.plot(t, result["omega_mag_deg_s"],
                       pen=pg.mkPen("#ffffff", width=2.2), name="|ω|")
        acquire = result.get("t_acquire_h")
        if acquire is not None:
            line = pg.InfiniteLine(pos=acquire, angle=90,
                                   pen=pg.mkPen("#aaaa55", style=Qt.PenStyle.DashLine),
                                   label="acquired")
            self.plot.addItem(line)
