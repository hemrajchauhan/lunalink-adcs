from PyQt6.QtWidgets import QWidget, QLabel, QVBoxLayout

class DisturbanceTorqueTab(QWidget):

    def __init__(self, parent = None):
        super().__init__(parent)
    
        layout = QVBoxLayout()
        layout.addWidget(QLabel("Disturbance Torque Plot"))
        self.setLayout(layout)