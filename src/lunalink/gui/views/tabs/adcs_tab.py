from PyQt6.QtWidgets import QWidget, QLabel, QVBoxLayout

class ADCSTab(QWidget):

    def __init__(self, parent = None):
        super().__init__(parent)
    
        layout = QVBoxLayout()
        layout.addWidget(QLabel("ADCS Settings"))
        self.setLayout(layout)