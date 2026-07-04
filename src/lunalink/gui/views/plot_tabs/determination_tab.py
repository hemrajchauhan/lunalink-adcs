import numpy as np
import pyqtgraph as pg
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel
from PyQt6.QtGui import QFont


class DeterminationTab(QWidget):
    """The determination half of ADCS (lecture Part 5): a gyro+star-tracker
    complementary filter. Splits the pointing budget into KNOWLEDGE error
    (estimate vs truth) and CONTROL error (truth vs command), and shows the
    gyro-bias estimate converging."""

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
        self.plot.setLogMode(y=True)
        self.plot.setLabel("left", "Error", units="°")
        self.plot.setLabel("bottom", "Time", units="h")
        self.plot.setTitle("Pointing budget: knowledge vs control error",
                           color="#e6e6e6", size="10pt")
        self.plot.addLegend()
        layout.addWidget(self.plot, stretch=3)

        self.summary = QLabel("")
        self.summary.setFont(QFont("Consolas", 9))
        self.summary.setStyleSheet("color: #cfd6e4; padding: 4px;")
        layout.addWidget(self.summary, stretch=2)

    def _refresh(self, result):
        det = result.get("determination")
        if not det or "knowledge_error_deg" not in result:
            return
        self.hint.hide()
        self.plot.clear()
        t = result["t_h"]
        self.plot.plot(t, result["knowledge_error_deg"],
                       pen=pg.mkPen("#ff5370", width=2), name="knowledge (est vs truth)")
        self.plot.plot(t, result["attitude_error_deg"],
                       pen=pg.mkPen("#ffb86c", width=2), name="control (truth vs cmd)")

        # Knowledge budget line (log-y plot: position is log10 of the value).
        budget_line = pg.InfiniteLine(
            pos=np.log10(det["knowledge_budget_deg"]), angle=0,
            pen=pg.mkPen("#6fae6f", style=Qt.PenStyle.DashLine),
            label=f"knowledge budget {det['knowledge_budget_deg']:g}°",
            labelOpts={"color": "#6fae6f", "position": 0.05})
        self.plot.addItem(budget_line)

        ok = "PASS" if det["knowledge_rms_deg"] <= det["knowledge_budget_deg"] else "OVER"
        lines = [
            "ATTITUDE DETERMINATION  (gyro + star tracker, complementary filter)",
            f"  Gyro bias learned : {det['bias_initial_deg_hr']:.2f} "
            f"→ {det['bias_final_deg_hr']:.3f} °/hr",
            "",
            "POINTING BUDGET          measured     budget",
            f"  Knowledge error (RMS)  {det['knowledge_rms_deg']:.4f}°     "
            f"{det['knowledge_budget_deg']:.2f}°   [{ok}]",
            f"  Control error   (RMS)  {det['control_rms_deg']:.4f}°     "
            f"{det['control_budget_deg']:.2f}°",
            f"  Total pointing         {det['pointing_total_deg']:.4f}°     "
            f"{det['total_budget_deg']:.2f}°",
            f"  (star-tracker noise floor {det['star_tracker_noise_deg']:.4f}°)",
        ]
        self.summary.setText("\n".join(lines))
