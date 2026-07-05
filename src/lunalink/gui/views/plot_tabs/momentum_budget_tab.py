"""The momentum budget ("momentum wall"): the cumulative disturbance
angular-momentum demand, split into what the wheels must STORE per orbit
(cyclic swing) and what the magnetorquers must DUMP per day (secular drift).
"""
from .base_plot_tab import BasePlotTab
from . import style


class MomentumBudgetTab(BasePlotTab):

    TITLE = "Disturbance momentum demand: wiggle is cyclic, climb is secular"
    LEFT_LABEL = ("|∫ T_dist dt|", "N·m·s")

    def update_plot(self, result):
        if "dist_momentum_nms" not in result:
            return
        self.plot.plot(result["t_h"], result["dist_momentum_nms"],
                       pen=style.line_pen(style.SERIES["momentum"], 2.2),
                       name="cumulative demand")
        eclipse = result.get("eclipse")
        if eclipse is not None:
            style.shade_intervals(self.plot, result["t_h"], eclipse)

    def build_summary(self, result):
        budget = result.get("momentum_budget") or {}
        if not budget:
            return None
        slew = budget.get("slew_momentum_nms", 0.0)
        slew_angle = budget.get("slew_angle_deg") or 90.0
        cyclic = budget["cyclic_swing_nms"]
        driver = "slew" if slew >= cyclic else "disturbance"
        rows = [
            ("Cyclic swing per orbit (wheels STORE)",
             f"±{style.fmt(cyclic, 'N·m·s')}"),
            (f"Slew demand ({slew_angle:.0f}° rest-to-rest)",
             f"{style.fmt(slew, 'N·m·s')} &nbsp;<i>[{driver}-driven]</i>"),
            ("Secular drift per day (torquers DUMP)",
             style.fmt(budget["secular_per_day_nms"], "N·m·s/day")),
            ("Recommended wheel capacity (×1.5 margin)",
             style.fmt(budget["recommended_wheel_hmax_nms"], "N·m·s"),
             style.GOOD),
            ("Minimum dump dipole (best case, ⊥ B)",
             style.fmt(budget["dump_dipole_am2"], "A·m²"), style.GOOD),
        ]
        note = ("Cyclic torque is borrowed and returned every orbit, so it "
                "sizes the wheels. Secular torque never averages out; it must "
                "be dumped against the geomagnetic field, which sizes the "
                "magnetorquers.")
        return style.summary_html("Momentum budget", rows, note)
