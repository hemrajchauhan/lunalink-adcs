from PyQt6.QtWidgets import QWidget, QLabel, QVBoxLayout

class RWMomentumTab(QWidget):

    def __init__(self, parent = None):
        super().__init__(parent)
    
        layout = QVBoxLayout()
        layout.addWidget(QLabel("Reaction Wheel Momentum Plot"))
        self.setLayout(layout)