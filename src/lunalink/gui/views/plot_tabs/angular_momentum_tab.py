"""Total angular momentum |H| = |I·ω + h_wheels| — the integrator/consistency
check — alongside the wheel share of that momentum."""
import numpy as np

from .base_plot_tab import BasePlotTab
from . import style


class AngularMomentumTab(BasePlotTab):

    TITLE = "Total angular momentum (consistency check)"
    LEFT_LABEL = ("Angular momentum", "N·m·s")

    def update_plot(self, result):
        t = result["t_h"]
        self.plot.plot(t, result["angular_momentum_nms"],
                       pen=style.line_pen(style.SERIES["momentum"], 2.2),
                       name="|H| body + wheels")
        self.plot.plot(t, result["wheel_momentum_mag_nms"],
                       pen=style.line_pen(style.SERIES["wheel"], 1.3),
                       name="|h| wheels only")

    def build_summary(self, result):
        H = result["angular_momentum_nms"]
        rows = [
            ("Initial |H|", style.fmt(float(H[0]), "N·m·s")),
            ("Final |H|", style.fmt(float(H[-1]), "N·m·s")),
            ("Peak |H|", style.fmt(float(np.max(H)), "N·m·s")),
        ]
        note = ("Reaction wheels only exchange momentum internally, so |H| "
                "changes only through <i>external</i> torques: disturbances "
                "and the magnetorquers (detumbling and desaturation). A "
                "smooth, physically explainable |H| curve is the standard "
                "sanity check that the integrator and the torque bookkeeping "
                "agree.")
        return style.summary_html("Momentum bookkeeping", rows, note)
