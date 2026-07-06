"""The tabbed panel that hosts all ADCS result plots.

The panel stays hidden until the first simulation finishes (it would only
waste space before that) and carries a close button so the user can put it
away after viewing; the main window re-shows it on the next run or via the
"Show simulation results" bar.
"""
from PyQt6.QtCore import pyqtSignal
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QTabWidget, QToolButton,
)

from .plot_tabs.angular_velocity_tab import AngularVelocityTab
from .plot_tabs.attitude_error_tab import AttitudeErrorTab
from .plot_tabs.rw_momentum_tab import RWMomentumTab
from .plot_tabs.disturbance_torque_tab import DisturbanceTorqueTab
from .plot_tabs.angular_momentum_tab import AngularMomentumTab
from .plot_tabs.momentum_budget_tab import MomentumBudgetTab
from .plot_tabs.determination_tab import DeterminationTab


class PlotPanel(QWidget):

    closeRequested = pyqtSignal()    # user clicked the panel's close button
    resultsUpdated = pyqtSignal()    # new simulation results were loaded

    def __init__(self, parent=None):
        super().__init__(parent)
        self._create_widgets()
        self._create_layout()

    def _create_widgets(self):
        # Header: title + close button.
        self.header_label = QLabel("Simulation Results")
        self.header_label.setStyleSheet(
            "font-weight: 600; color: #46a0ff; padding: 1px 4px;")

        self.close_button = QToolButton()
        self.close_button.setText("✕")            # multiplication X
        self.close_button.setToolTip(
            "Hide the results panel. It reopens automatically after the "
            "next simulation run, or via the 'Show simulation results' bar.")
        self.close_button.setStyleSheet(
            "QToolButton { border: none; color: #8a93a6; font-size: 14px;"
            "              padding: 1px 7px; border-radius: 4px; }"
            "QToolButton:hover { color: #e8ebf2; background: #2a3145; }")
        self.close_button.clicked.connect(self.closeRequested.emit)

        self.tab_widget = QTabWidget()

        self.angular_velocity_tab = AngularVelocityTab()
        self.attitude_error_tab = AttitudeErrorTab()
        self.rw_momentum_tab = RWMomentumTab()
        self.disturbance_torque_tab = DisturbanceTorqueTab()
        self.angular_momentum_tab = AngularMomentumTab()
        self.momentum_budget_tab = MomentumBudgetTab()
        self.determination_tab = DeterminationTab()

    def _create_layout(self):
        tabs = [
            (self.angular_velocity_tab, "Angular Velocity",
             "Body rotation rate over time (shows detumbling)."),
            (self.attitude_error_tab, "Pointing Error",
             "Angle between the spacecraft and its target direction."),
            (self.rw_momentum_tab, "Wheel Momentum",
             "Reaction-wheel stored momentum and desaturation."),
            (self.disturbance_torque_tab, "Disturbance Torques",
             "External torques acting on the spacecraft along the orbit."),
            (self.angular_momentum_tab, "Total Momentum",
             "Total angular momentum (an integrator sanity check)."),
            (self.momentum_budget_tab, "Momentum Budget",
             "How much momentum the wheels must store and the torquers remove."),
            (self.determination_tab, "Pointing Budget",
             "Knowledge error vs control error and gyro-bias convergence."),
        ]
        for widget, title, tip in tabs:
            index = self.tab_widget.addTab(widget, title)
            self.tab_widget.setTabToolTip(index, tip)

        header = QHBoxLayout()
        header.setContentsMargins(2, 2, 2, 0)
        header.addWidget(self.header_label)
        header.addStretch()
        header.addWidget(self.close_button)

        layout = QVBoxLayout()
        layout.setContentsMargins(4, 4, 4, 4)
        layout.setSpacing(2)
        layout.addLayout(header)
        layout.addWidget(self.tab_widget)
        self.setLayout(layout)

    def update_results(self, result: dict):
        """Push a new ADCS simulation result to every plot tab."""
        for tab in (self.angular_velocity_tab, self.attitude_error_tab,
                    self.rw_momentum_tab, self.disturbance_torque_tab,
                    self.angular_momentum_tab, self.momentum_budget_tab,
                    self.determination_tab):
            tab.refresh(result)
        self.resultsUpdated.emit()
