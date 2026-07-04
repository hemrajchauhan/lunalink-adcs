"""Attitude (pointing) error versus the commanded attitude, with the
acquisition threshold and the moment it was first met."""
import numpy as np

from .base_plot_tab import BasePlotTab
from . import style

_TITLES = {
    "slew": "Slew attitude error — angle to the commanded attitude",
    "detumble": "Attitude error vs the Sun line (uncontrolled during detumble)",
    "full": "Attitude error — detumble, then Sun acquisition and hold",
    "sun_pointing": "Sun-pointing attitude error",
}


class AttitudeErrorTab(BasePlotTab):

    TITLE = "Attitude error"
    LEFT_LABEL = ("Pointing error", "°")

    def update_plot(self, result):
        style.set_title(self.plot, _TITLES.get(result.get("mode"), self.TITLE))
        self.plot.plot(result["t_h"], result["attitude_error_deg"],
                       pen=style.line_pen(style.SERIES["error"], 2.0),
                       name="pointing error")
        threshold = result.get("acquire_threshold_deg")
        if threshold is not None:
            style.h_marker(self.plot, threshold, style.GOOD,
                           f"acquired below {threshold:g}°")
        acquire = result.get("t_acquire_h")
        if acquire is not None:
            style.v_marker(self.plot, acquire, style.GOOD, "acquired")

    def build_summary(self, result):
        err = result["attitude_error_deg"]
        tail = err[-max(1, len(err) // 4):]          # converged last quarter
        rows = [
            ("Initial error", style.fmt(float(err[0]), "°")),
            ("Final error", style.fmt(float(err[-1]), "°")),
            ("RMS error (last quarter)", style.fmt(float(np.sqrt(np.mean(tail ** 2))), "°")),
        ]
        acquire = result.get("t_acquire_h")
        threshold = result.get("acquire_threshold_deg")
        if acquire is not None and threshold is not None:
            rows.append((f"First below {threshold:g}°",
                         style.fmt(acquire, "h"), style.GOOD))
        return style.summary_html("Pointing performance", rows)
