import pyqtgraph as pg

from .base_plot_tab import BasePlotTab


class DisturbanceTorqueTab(BasePlotTab):

    TITLE = "Disturbance torques vs orbit (GG at perigee, SRP at apogee)"
    LEFT_LABEL = ("Torque", "N·m")

    def update_plot(self, result):
        t = result["t_h"]
        series = [
            ("T_gg_nm", "#ff6b6b", "gravity gradient"),
            ("T_srp_nm", "#ffd24d", "solar pressure"),
            ("T_mag_nm", "#5b9bff", "magnetic"),
            ("T_aero_nm", "#5cd65c", "aerodynamic"),
            ("disturbance_nm", "#ffffff", "total"),
        ]
        for key, color, name in series:
            if key in result:
                width = 2.0 if key == "disturbance_nm" else 1.3
                self.plot.plot(t, result[key], pen=pg.mkPen(color, width=width), name=name)
        self.plot.setLogMode(x=False, y=True)
