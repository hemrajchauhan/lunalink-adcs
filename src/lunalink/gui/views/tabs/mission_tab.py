from PyQt6.QtWidgets import QWidget, QLabel, QVBoxLayout

class MissionTab(QWidget):

    def __init__(self, parent = None):
        super().__init__(parent)

        layout = QVBoxLayout()
        layout.addWidget(QLabel("Mission Settings"))
        self.setLayout(layout)