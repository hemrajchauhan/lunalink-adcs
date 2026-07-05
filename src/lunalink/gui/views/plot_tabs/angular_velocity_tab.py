"""Body angular velocity: per-axis rates, the rate magnitude, and the moment
the pointing target was acquired."""
import numpy as np

from .base_plot_tab import BasePlotTab
from . import style

_TITLES = {
    "detumble": "Body angular velocity: detumbling convergence",
    "full": "Body angular velocity: detumble, then pointing",
    "slew": "Body angular velocity: slew rate profile",
    "sun_pointing": "Body angular velocity: rate damping while pointing",
}


class AngularVelocityTab(BasePlotTab):

    TITLE = "Body angular velocity"
    LEFT_LABEL = ("Angular velocity", "°/s")

    def update_plot(self, result):
        style.set_title(self.plot, _TITLES.get(result.get("mode"), self.TITLE))
        t = result["t_h"]
        omega = result["omega_deg_s"]
        for i, axis in enumerate("xyz"):
            self.plot.plot(t, omega[:, i],
                           pen=style.line_pen(style.SERIES[axis], 1.3),
                           name=f"ω{axis}")
        self.plot.plot(t, result["omega_mag_deg_s"],
                       pen=style.line_pen(style.SERIES["mag"], 2.2), name="|ω|")
        acquire = result.get("t_acquire_h")
        if acquire is not None:
            style.v_marker(self.plot, acquire, style.GOOD, "acquired")

    def build_summary(self, result):
        om = result["omega_mag_deg_s"]
        mode = result.get("mode", "")
        rows = [
            ("Initial rate", style.fmt(float(om[0]), "°/s")),
            ("Final rate", style.fmt(float(om[-1]), "°/s")),
            ("Peak rate", style.fmt(float(np.max(om)), "°/s")),
        ]
        acquire = result.get("t_acquire_h")
        if acquire is not None:
            rows.append(("Target acquired", style.fmt(acquire, "h"), style.GOOD))
        elif mode in ("detumble", "full"):
            rows.append(("Target acquired", "not within this run "
                         "(extend the duration)", style.WARN))
        note = ("B-dot detumbling only bites near perigee, where the "
                "geomagnetic field is strong; on a Molniya-type orbit the rate "
                "therefore drops in steps once per orbit."
                if mode in ("detumble", "full") else "")
        return style.summary_html("Rate history", rows, note)
