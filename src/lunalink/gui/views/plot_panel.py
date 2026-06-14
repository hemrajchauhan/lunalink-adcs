from PyQt6.QtWidgets  import QWidget, QVBoxLayout, QTabWidget

from .plot_tabs.angular_velocity_tab import AngularVelocityTab
from .plot_tabs.attitude_error_tab import AttitudeErrorTab
from .plot_tabs.rw_momentum_tab import RWMomentumTab
from .plot_tabs.disturbance_torque_tab import DisturbanceTorqueTab

class PlotPanel(QWidget):

    def __init__(self, parent=None):
        super().__init__(parent)
        self._create_widgets()
        self._create_layout()

    def _create_widgets(self):
        self.tab_widget = QTabWidget()

        self.angular_velocity_tab = AngularVelocityTab()
        self.attitude_error_tab = AttitudeErrorTab()
        self.rw_momentum_tab = RWMomentumTab()
        self.disturbance_torque_tab = DisturbanceTorqueTab()

    def _create_layout(self):
        self.tab_widget.addTab(self.angular_velocity_tab, "Angular Velocity")
        self.tab_widget.addTab(self.attitude_error_tab, "Attitude Error")
        self.tab_widget.addTab(self.rw_momentum_tab, "Reaction Wheel Momentum")
        self.tab_widget.addTab(self.disturbance_torque_tab, "Disturbance Torque")
        
        layout = QVBoxLayout()
        layout.addWidget(self.tab_widget)
        self.setLayout(layout)