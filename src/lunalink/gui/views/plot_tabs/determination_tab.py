"""Attitude determination (gyro + star tracker, complementary filter).

Top chart: knowledge error (estimate vs truth) against control error
(truth vs command) on a log scale, with the knowledge budget line.
Bottom chart: the gyro-bias estimate converging to the true bias.
"""
import pyqtgraph as pg

from .base_plot_tab import BasePlotTab
from . import style


class DeterminationTab(BasePlotTab):

    TITLE = "Pointing budget — knowledge vs control error"
    LEFT_LABEL = ("Error", "°")
    LOG_Y = True

    def __init__(self, parent=None):
        super().__init__(parent)
        # Secondary chart: gyro-bias estimation error.
        self.bias_plot = style.make_plot(
            "Gyro-bias estimate convergence",
            left=("Bias error", "°/h"), bottom=("Time", "h"))
        self.bias_plot.setXLink(self.plot)
        self.layout().insertWidget(2, self.bias_plot, stretch=3)

    def update_plot(self, result):
        det = result.get("determination")
        self.bias_plot.clear()
        if not det or "knowledge_error_deg" not in result:
            style.set_title(self.plot, "Attitude determination — estimator "
                                       "disabled for this run")
            return
        t = result["t_h"]
        self.plot.plot(t, result["knowledge_error_deg"],
                       pen=style.line_pen(style.SERIES["knowledge"], 1.6),
                       name="knowledge (estimate vs truth)")
        self.plot.plot(t, result["attitude_error_deg"],
                       pen=style.line_pen(style.SERIES["control"], 1.6),
                       name="control (truth vs command)")
        style.h_marker(self.plot, det["knowledge_budget_deg"], style.GOOD,
                       f"knowledge budget {det['knowledge_budget_deg']:g}°",
                       log_y=True)
        self.bias_plot.plot(t, result["gyro_bias_error_deg_hr"],
                            pen=style.line_pen(style.SERIES["bias"], 1.8),
                            name="|b̂ − b_true|")

    def build_summary(self, result):
        det = result.get("determination")
        if not det:
            return None
        know_ok = det["knowledge_rms_deg"] <= det["knowledge_budget_deg"]
        total_ok = det["pointing_total_deg"] <= det["total_budget_deg"]
        rows = [
            ("Knowledge error (RMS, converged tail)",
             f"{style.fmt(det['knowledge_rms_deg'], '°', 3)} of "
             f"{det['knowledge_budget_deg']:g}° budget "
             + style.badge("PASS" if know_ok else "OVER", know_ok)),
            ("Control error (RMS, converged tail)",
             f"{style.fmt(det['control_rms_deg'], '°', 3)} of "
             f"{det['control_budget_deg']:g}° budget"),
            ("Total pointing (knowledge + control)",
             f"{style.fmt(det['pointing_total_deg'], '°', 3)} of "
             f"{det['total_budget_deg']:g}° budget "
             + style.badge("PASS" if total_ok else "OVER", total_ok)),
            ("Gyro bias learned",
             f"{det['bias_initial_deg_hr']:.2f} → "
             f"{det['bias_final_deg_hr']:.3f} °/h", style.GOOD),
            ("Star-tracker noise floor",
             style.fmt(det["star_tracker_noise_deg"], "°", 3)),
        ]
        note = ("The filter integrates the fast-but-drifting gyro and resets "
                "the drift with each star-tracker fix, learning the gyro bias "
                "from the repeated residuals — knowledge error settles at the "
                "star-tracker noise floor.")
        return style.summary_html("Attitude determination", rows, note)
