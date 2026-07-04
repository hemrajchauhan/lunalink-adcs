"""Disturbance torques along the orbit (log scale), with eclipse intervals
shaded so the solar-pressure drop-outs are self-explanatory."""
from .base_plot_tab import BasePlotTab
from . import style

_SERIES = [
    ("T_gg_nm", "gg", "gravity gradient", 1.3),
    ("T_srp_nm", "srp", "solar pressure", 1.3),
    ("T_mag_nm", "magdist", "magnetic", 1.3),
    ("T_aero_nm", "aero", "aerodynamic", 1.3),
    ("disturbance_nm", "mag", "total", 2.2),
]


class DisturbanceTorqueTab(BasePlotTab):

    TITLE = "Disturbance torques along the orbit"
    LEFT_LABEL = ("Torque", "N·m")
    LOG_Y = True

    def update_plot(self, result):
        t = result["t_h"]
        for key, color, name, width in _SERIES:
            if key in result:
                self.plot.plot(t, result[key],
                               pen=style.line_pen(style.SERIES[color], width),
                               name=name)
        eclipse = result.get("eclipse")
        if eclipse is not None:
            style.shade_intervals(self.plot, t, eclipse)

    def build_summary(self, result):
        hierarchy = result.get("disturbance_hierarchy") or []
        rows = []
        for entry in hierarchy:
            rows.append((entry["source"],
                         f"peak {style.fmt(entry['peak_nm'], 'N·m')} "
                         f"&nbsp;·&nbsp; perigee {style.fmt(entry['perigee_nm'], 'N·m')} "
                         f"&nbsp;·&nbsp; apogee {style.fmt(entry['apogee_nm'], 'N·m')} "
                         f"&nbsp;·&nbsp; <i>{entry['behaviour']}</i>"))
        note = ("Shaded bands are eclipse passes — solar-radiation-pressure "
                "torque vanishes there. Gravity-gradient, magnetic and "
                "aerodynamic torques all spike at perigee (∝ 1/r³ or denser "
                "air), while SRP dominates the long apogee arcs.")
        return style.summary_html(
            "Disturbance hierarchy (largest first)", rows, note)
