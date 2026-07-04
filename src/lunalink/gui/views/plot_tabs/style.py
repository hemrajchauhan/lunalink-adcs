"""Shared look-and-feel for all ADCS result plots.

Every plot tab draws from this module so the whole Plots panel stays visually
consistent: one background, one grid style, one title/axis typography, one
series palette, and shared helpers for reference lines, event markers,
eclipse shading and the HTML summaries shown beneath the charts.
"""
import numpy as np
import pyqtgraph as pg
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor, QFont

pg.setConfigOptions(antialias=True)

# -- palette ----------------------------------------------------------------
BACKGROUND = "#10141d"
AXIS_COLOR = "#8a93a6"          # axis lines, tick labels
TEXT_COLOR = "#e8ebf2"          # titles
MUTED = "#8a93a6"               # hints, secondary text
GRID_ALPHA = 0.18

GOOD = "#5fb878"                # pass / acquired / thresholds met
WARN = "#c8a24a"                # triggers, cautions
BAD = "#e06c75"                 # limits, failures
ECLIPSE = (90, 110, 160, 40)    # translucent shading for eclipse intervals

SERIES = {
    "x": "#ff6b6b",
    "y": "#4ecf7d",
    "z": "#5b9bff",
    "mag": "#f5f7fa",           # magnitude / total traces
    "error": "#ffb347",
    "wheel": "#46e0a0",
    "momentum": "#b388ff",
    "srp": "#ffd24d",
    "gg": "#ff6b6b",
    "magdist": "#5b9bff",
    "aero": "#4ecf7d",
    "knowledge": "#ff5370",
    "control": "#ffb86c",
    "bias": "#6fb3ff",
}

_TITLE_SIZE = "11pt"
_AXIS_FONT = QFont("Segoe UI", 9)


# -- construction -------------------------------------------------------------
def make_plot(title: str = "", left=("y", ""), bottom=("Time", "h"),
              log_y: bool = False) -> pg.PlotWidget:
    """A PlotWidget with the shared theme applied."""
    plot = pg.PlotWidget()
    plot.setBackground(BACKGROUND)
    plot.showGrid(x=True, y=True, alpha=GRID_ALPHA)
    for side in ("left", "bottom"):
        axis = plot.getAxis(side)
        axis.setPen(pg.mkPen(AXIS_COLOR))
        axis.setTextPen(pg.mkPen(AXIS_COLOR))
        axis.setStyle(tickFont=_AXIS_FONT)
    plot.setLabel("left", left[0], units=left[1],
                  color=AXIS_COLOR, **{"font-size": "10pt"})
    plot.setLabel("bottom", bottom[0], units=bottom[1],
                  color=AXIS_COLOR, **{"font-size": "10pt"})
    if title:
        set_title(plot, title)
    if log_y:
        plot.setLogMode(y=True)
    legend = plot.addLegend(offset=(-8, 6), labelTextColor="#cfd6e4",
                            brush=pg.mkBrush(16, 20, 29, 200),
                            pen=pg.mkPen(58, 68, 92, 120))
    legend.setLabelTextSize("9pt")
    return plot


def set_title(plot: pg.PlotWidget, text: str) -> None:
    plot.setTitle(text, color=TEXT_COLOR, size=_TITLE_SIZE)


def line_pen(color: str, width: float = 1.6) -> pg.mkPen:
    return pg.mkPen(color, width=width)


# -- reference lines and event markers ----------------------------------------
def h_marker(plot, value: float, color: str, label: str = "",
             dotted: bool = False, log_y: bool = False,
             label_pos: float = 0.03) -> None:
    """Horizontal reference line (limit, threshold, budget).

    With ``log_y`` the plot is in log mode and the line position must be the
    log10 of the data value.
    """
    if log_y:
        if value <= 0:
            return
        value = float(np.log10(value))
    style = Qt.PenStyle.DotLine if dotted else Qt.PenStyle.DashLine
    plot.addItem(pg.InfiniteLine(
        pos=value, angle=0, pen=pg.mkPen(color, style=style, width=1.2),
        label=label or None,
        labelOpts={"color": color, "position": label_pos, "movable": False}))


def v_marker(plot, value: float, color: str, label: str = "",
             label_pos: float = 0.92) -> None:
    """Vertical event marker (acquisition, mode change)."""
    plot.addItem(pg.InfiniteLine(
        pos=value, angle=90,
        pen=pg.mkPen(color, style=Qt.PenStyle.DashLine, width=1.2),
        label=label or None,
        labelOpts={"color": color, "position": label_pos, "movable": False}))


def shade_intervals(plot, t: np.ndarray, mask: np.ndarray,
                    color=ECLIPSE) -> int:
    """Shade every contiguous True interval of ``mask`` (e.g. eclipses).
    Returns the number of intervals shaded."""
    mask = np.asarray(mask, dtype=bool)
    if mask.size == 0 or not mask.any():
        return 0
    # Build (start, end) index pairs of contiguous True runs.
    idx = np.flatnonzero(mask)
    breaks = np.flatnonzero(np.diff(idx) > 1)
    seg_starts = np.concatenate(([idx[0]], idx[breaks + 1]))
    seg_ends = np.concatenate((idx[breaks], [idx[-1]]))
    for s, e in zip(seg_starts, seg_ends):
        region = pg.LinearRegionItem(values=(t[s], t[e]), movable=False,
                                     brush=pg.mkBrush(*color),
                                     pen=pg.mkPen(None))
        region.setZValue(-10)
        plot.addItem(region)
    return len(seg_starts)


# -- HTML summaries ------------------------------------------------------------
def fmt(value, unit: str = "", digits: int = 3) -> str:
    """Compact numeric formatting for summary tables."""
    if value is None:
        return "—"
    if isinstance(value, str):
        return value
    magnitude = abs(value)
    if magnitude != 0 and (magnitude >= 1e4 or magnitude < 10 ** (-digits)):
        text = f"{value:.2e}"
    else:
        text = f"{value:.{digits}g}"
    return f"{text}&nbsp;{unit}" if unit else text


def summary_html(caption: str, rows, note: str = "") -> str:
    """A compact two-column summary table.

    ``rows`` is an iterable of (label, value_html) or
    (label, value_html, color) tuples.
    """
    cells = []
    for row in rows:
        label, value = row[0], row[1]
        color = row[2] if len(row) > 2 else TEXT_COLOR
        cells.append(
            f"<tr><td style='color:{MUTED}; padding:1px 14px 1px 0;'>{label}</td>"
            f"<td style='color:{color}; font-weight:600;'>{value}</td></tr>")
    note_html = (f"<div style='color:{MUTED}; margin-top:4px;'>{note}</div>"
                 if note else "")
    return (f"<div style='color:{TEXT_COLOR}; font-weight:600; "
            f"margin-bottom:3px;'>{caption}</div>"
            f"<table style='font-size:12px;'>{''.join(cells)}</table>{note_html}")


def badge(text: str, ok: bool) -> str:
    color = GOOD if ok else BAD
    return (f"<span style='color:{color}; border:1px solid {color}; "
            f"border-radius:3px; padding:0 5px;'>{text}</span>")
