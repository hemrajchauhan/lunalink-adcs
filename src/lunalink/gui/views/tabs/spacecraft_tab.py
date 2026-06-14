from PyQt6.QtWidgets import QWidget, QLabel, QVBoxLayout

class SpacecraftTab(QWidget):

    def __init__(self, parent = None):
        super().__init__(parent)
    
        layout = QVBoxLayout()
        layout.addWidget(QLabel("Spacecraft Settings"))
        self.setLayout(layout)