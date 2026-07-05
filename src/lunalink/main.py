"""GUI entry point for the LunaLink ADCS Simulator.

Usage:
    python -m lunalink.main
"""
from pathlib import Path
import sys

from PyQt6.QtGui import QIcon
from PyQt6.QtWidgets import QApplication

from lunalink.gui.main_window import MainWindow
from lunalink.gui.theme import DARK_STYLESHEET

_ICON = Path(__file__).parent / "gui" / "assets" / "icon.svg"


def main():
    app = QApplication(sys.argv)
    app.setApplicationName("LunaLink ADCS Simulator")
    app.setStyle("Fusion")
    app.setStyleSheet(DARK_STYLESHEET)
    if _ICON.exists():
        app.setWindowIcon(QIcon(str(_ICON)))

    window = MainWindow()
    # Start maximised: wide 3D scene on the left, controls and plots on the
    # right. The splitters stay fully user-adjustable afterwards.
    window.showMaximized()
    app.exec()


if __name__ == "__main__":
    sys.exit(main())
