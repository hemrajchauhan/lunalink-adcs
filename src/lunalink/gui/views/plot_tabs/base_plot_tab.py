"""Base class for the ADCS result plot tabs.

Provides the shared page layout: a themed pyqtgraph plot (built from
:mod:`style`), a hint shown until the first simulation run, and an optional
rich-text summary beneath the chart. Subclasses implement

    update_plot(result)            -- draw the series/markers
    build_summary(result) -> str   -- optional HTML for the summary area

where ``result`` is the dict returned by
:func:`lunalink.simulation.simulator.simulate`.
"""
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QScrollArea

from . import style


class BasePlotTab(QWidget):

    TITLE = "Plot"
    LEFT_LABEL = ("y", "")
    BOTTOM_LABEL = ("Time", "h")
    LOG_Y = False

    def __init__(self, parent=None):
        super().__init__(parent)
        outer = QVBoxLayout(self)
        outer.setContentsMargins(6, 6, 6, 6)
        outer.setSpacing(4)

        self.hint = QLabel("Run a simulation (ADCS Simulation tab or the "
                           "Mission tab) to populate this plot.")
        self.hint.setStyleSheet(f"color: {style.MUTED}; padding: 2px;")
        self.hint.setWordWrap(True)
        outer.addWidget(self.hint)

        # Charts keep a readable minimum height; when the panel is smaller
        # than the content (e.g. tabs with two charts plus a summary), the
        # page scrolls vertically instead of squashing the plots.
        content = QWidget()
        self.content_layout = QVBoxLayout(content)
        self.content_layout.setContentsMargins(0, 0, 0, 0)
        self.content_layout.setSpacing(6)

        self.plot = style.make_plot(self.TITLE, self.LEFT_LABEL,
                                    self.BOTTOM_LABEL, log_y=self.LOG_Y)
        self.content_layout.addWidget(self.plot, stretch=5)

        self.summary = QLabel("")
        self.summary.setTextFormat(Qt.TextFormat.RichText)
        self.summary.setWordWrap(True)
        self.summary.setStyleSheet("padding: 4px 6px;")
        self.summary.hide()
        self.content_layout.addWidget(self.summary, stretch=0)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QScrollArea.Shape.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setWidget(content)
        outer.addWidget(scroll)

    # -- subclass hooks -----------------------------------------------------
    def update_plot(self, result: dict) -> None:
        raise NotImplementedError

    def build_summary(self, result: dict) -> str | None:
        return None

    # -- refresh contract (called by PlotPanel) --------------------------------
    def refresh(self, result: dict) -> None:
        self.hint.hide()
        self.plot.clear()
        self.update_plot(result)
        html = self.build_summary(result)
        if html:
            self.summary.setText(html)
            self.summary.show()
        else:
            self.summary.hide()

    # Backwards-compatible alias.
    _refresh = refresh
