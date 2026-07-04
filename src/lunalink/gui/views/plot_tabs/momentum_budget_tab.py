import pyqtgraph as pg
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel
from PyQt6.QtGui import QFont


class MomentumBudgetTab(QWidget):
    """The 'momentum wall' (lecture Part 3): how much momentum the wheels must
    STORE (cyclic swing/orbit) and the torquers must REMOVE (secular/day), plus
    the disturbance hierarchy with each source classified secular vs cyclic."""

    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)

        self.hint = QLabel("Run the simulation from the ADCS Control tab.")
        self.hint.setStyleSheet("color: #888; padding: 2px;")
        layout.addWidget(self.hint)

        self.plot = pg.PlotWidget()
        self.plot.setBackground("#10131c")
        self.plot.showGrid(x=True, y=True, alpha=0.25)
        self.plot.setLabel("left", "|∫T_dist dt|", units="N·m·s")
        self.plot.setLabel("bottom", "Time", units="h")
        self.plot.setTitle("Disturbance angular-momentum demand "
                           "(wiggle = cyclic, climb = secular)",
                           color="#e6e6e6", size="10pt")
        layout.addWidget(self.plot, stretch=3)

        self.summary = QLabel("")
        self.summary.setFont(QFont("Consolas", 9))
        self.summary.setStyleSheet("color: #cfd6e4; padding: 4px;")
        layout.addWidget(self.summary, stretch=2)

    def _refresh(self, result):
        self.hint.hide()
        self.plot.clear()
        if "dist_momentum_nms" in result:
            self.plot.plot(result["t_h"], result["dist_momentum_nms"],
                           pen=pg.mkPen("#b388ff", width=2), name="demand")

        budget = result.get("momentum_budget") or {}
        hierarchy = result.get("disturbance_hierarchy") or []

        lines = ["MOMENTUM BUDGET  (the 'momentum wall')"]
        if budget:
            slew = budget.get("slew_momentum_nms", 0.0)
            slew_angle = budget.get("slew_angle_deg") or 90.0
            driver = "slew" if slew >= budget["cyclic_swing_nms"] else "disturbance"
            lines += [
                f"  Cyclic disturbance swing / orbit (STORE):  ±{budget['cyclic_swing_nms']:.3f} N·m·s",
                f"  Slew demand ({slew_angle:.0f}°):{'':<21}{slew:.2f} N·m·s   [{driver}-driven]",
                f"  Secular momentum / day (DUMP):             {budget['secular_per_day_nms']:.3f} N·m·s/day",
                f"  → wheels: h_max ≳ {budget['recommended_wheel_hmax_nms']:.2f} N·m·s"
                f"    torquers: dipole ≳ {budget['dump_dipole_am2']:.0f} A·m²",
            ]
        lines.append("")
        lines.append(f"DISTURBANCE HIERARCHY     {'peak':>9} {'perigee':>9} {'apogee':>9}  behaviour")
        for e in hierarchy:
            lines.append(
                f"  {e['source']:<20} {e['peak_nm']:>9.2e} {e['perigee_nm']:>9.2e} "
                f"{e['apogee_nm']:>9.2e}  {e['behaviour']}")
        self.summary.setText("\n".join(lines))
