import pyqtgraph as pg
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel


class BasePlotTab(QWidget):
    """A pyqtgraph plot with a title, axis labels and a legend.

    Subclasses implement :meth:`update_plot(result)` where ``result`` is the
    dict returned by :func:`lunalink.simulation.adcs.simulate`.
    """

    TITLE = "Plot"
    LEFT_LABEL = ("y", "")
    BOTTOM_LABEL = ("Time", "h")

    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)

        self.plot = pg.PlotWidget()
        self.plot.setBackground("#10131c")
        self.plot.showGrid(x=True, y=True, alpha=0.25)
        self.plot.addLegend(offset=(-10, 10))
        self.plot.setLabel("left", self.LEFT_LABEL[0], units=self.LEFT_LABEL[1])
        self.plot.setLabel("bottom", self.BOTTOM_LABEL[0], units=self.BOTTOM_LABEL[1])
        self.plot.setTitle(self.TITLE, color="#e6e6e6", size="11pt")

        self.hint = QLabel("Run the simulation from the ADCS Control tab.")
        self.hint.setStyleSheet("color: #888; padding: 2px;")

        layout.addWidget(self.hint)
        layout.addWidget(self.plot)

    def update_plot(self, result: dict):
        raise NotImplementedError

    def _refresh(self, result: dict):
        self.plot.clear()
        self.hint.hide()
        self.update_plot(result)
