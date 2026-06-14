from PyQt6.QtWidgets import QWidget, QLabel, QVBoxLayout

class AttitudeErrorTab(QWidget):

    def __init__(self, parent = None):
        super().__init__(parent)
    
        layout = QVBoxLayout()
        layout.addWidget(QLabel("Attitude Error Plot"))
        self.setLayout(layout)