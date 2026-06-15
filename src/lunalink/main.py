from PyQt6.QtWidgets import QApplication
import sys

from lunalink.gui.main_window import MainWindow
from lunalink.gui.theme import DARK_STYLESHEET


def main():
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    app.setStyleSheet(DARK_STYLESHEET)
    window = MainWindow()
    window.show()
    app.exec()


if __name__ == "__main__":
    sys.exit(main())
