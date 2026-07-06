"""Spacecraft orientation: roll/pitch/yaw (3-2-1 Euler angles) versus time,
computed from the simulated attitude quaternion."""
import numpy as np

from .base_plot_tab import BasePlotTab
from . import style

_TITLES = {
    "detumble": "Orientation (roll/pitch/yaw): free tumbling",
    "full": "Orientation (roll/pitch/yaw): tumble, then Sun hold",
    "slew": "Orientation (roll/pitch/yaw): commanded reorientation",
    "sun_pointing": "Orientation (roll/pitch/yaw): Sun acquisition and hold",
}


class OrientationTab(BasePlotTab):

    TITLE = "Spacecraft orientation (Euler angles)"
    LEFT_LABEL = ("Angle", "°")

    def update_plot(self, result):
        style.set_title(self.plot, _TITLES.get(result.get("mode"), self.TITLE))
        t = result["t_h"]
        euler = result["euler_deg"]
        for i, (name, key) in enumerate((("roll", "x"), ("pitch", "y"),
                                         ("yaw", "z"))):
            self.plot.plot(t, euler[:, i],
                           pen=style.line_pen(style.SERIES[key], 1.4),
                           name=name)

    def build_summary(self, result):
        euler = result["euler_deg"]
        mode = result.get("mode", "")
        rows = [
            ("Initial (roll, pitch, yaw)",
             "({:.1f}, {:.1f}, {:.1f})°".format(*euler[0])),
            ("Final (roll, pitch, yaw)",
             "({:.1f}, {:.1f}, {:.1f})°".format(*euler[-1])),
        ]
        if mode in ("detumble", "full"):
            note = ("Angles are the 3-2-1 (yaw-pitch-roll) rotation from the "
                    "inertial frame to the body frame. While tumbling they "
                    "sweep and wrap at ±180°, so the vertical jumps are the "
                    "wrap-around, not physical motion.")
        else:
            note = ("Angles are the 3-2-1 (yaw-pitch-roll) rotation from the "
                    "inertial frame to the body frame. A steady hold appears "
                    "as three constant lines; their values are set by the "
                    "commanded attitude, not by zero.")
        return style.summary_html("Attitude in Euler angles", rows, note)
