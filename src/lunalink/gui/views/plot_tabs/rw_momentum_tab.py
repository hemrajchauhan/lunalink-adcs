"""Reaction-wheel stored momentum: per-axis wheel momentum, the magnitude,
the per-wheel capacity and the desaturation trigger level."""
import numpy as np

from .base_plot_tab import BasePlotTab
from . import style


class RWMomentumTab(BasePlotTab):

    TITLE = "Reaction-wheel stored momentum"
    LEFT_LABEL = ("Wheel momentum", "N·m·s")

    def update_plot(self, result):
        t = result["t_h"]
        hw = result.get("wheel_momentum_nms")
        if hw is not None:
            for i, axis in enumerate("xyz"):
                self.plot.plot(t, hw[:, i],
                               pen=style.line_pen(style.SERIES[axis], 1.1),
                               name=f"h {axis}")
        self.plot.plot(t, result["wheel_momentum_mag_nms"],
                       pen=style.line_pen(style.SERIES["wheel"], 2.2),
                       name="|h| total")
        capacity = result.get("rw_capacity_nms")
        if capacity is not None:
            style.h_marker(self.plot, capacity, style.BAD, "per-wheel capacity")
        trigger = result.get("desat_trigger_nms")
        if trigger is not None:
            style.h_marker(self.plot, trigger, style.WARN,
                           "desaturation trigger", dotted=True, label_pos=0.35)

    def build_summary(self, result):
        mag = result["wheel_momentum_mag_nms"]
        capacity = result.get("rw_capacity_nms")
        peak = float(np.max(mag))
        rows = [
            ("Peak stored momentum", style.fmt(peak, "N·m·s")),
            ("Momentum at end of run", style.fmt(float(mag[-1]), "N·m·s")),
        ]
        if capacity:
            saturated = peak >= 0.999 * capacity
            rows.append(("Wheel utilisation",
                         f"{100.0 * peak / capacity:.0f}% of capacity "
                         + style.badge("SATURATED" if saturated else "OK",
                                       not saturated),
                         style.BAD if saturated else style.GOOD))
        note = ("Momentum builds up from secular disturbance torque and is "
                "unloaded magnetically (most effectively near perigee, where "
                "the field is strongest) once it crosses the trigger level.")
        return style.summary_html("Wheel loading", rows, note)
