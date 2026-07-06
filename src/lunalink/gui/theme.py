"""A single modern dark theme for the whole application (Qt stylesheet)."""

ACCENT = "#46a0ff"

DARK_STYLESHEET = f"""
* {{
    font-family: "Segoe UI", "Inter", system-ui, sans-serif;
    font-size: 13px;
    color: #e6e9ef;
}}
QWidget {{
    background-color: #11151f;
}}
QToolTip {{
    background-color: #f4f7fb;
    color: #0d111a;
    border: 1px solid {ACCENT};
    border-radius: 4px;
    padding: 5px 8px;
    font-size: 12px;
}}
QMainWindow, QDialog {{
    background-color: #0d111a;
}}
QGroupBox {{
    border: 1px solid #283042;
    border-radius: 8px;
    margin-top: 14px;
    padding: 10px 8px 8px 8px;
    background-color: #161b27;
}}
QGroupBox::title {{
    subcontrol-origin: margin;
    left: 12px;
    padding: 0 4px;
    color: {ACCENT};
    font-weight: 600;
}}
QTabWidget::pane {{
    border: 1px solid #283042;
    border-radius: 8px;
    top: -1px;
}}
QTabBar::tab {{
    background: #161b27;
    color: #9aa4b6;
    padding: 7px 14px;
    border: 1px solid #283042;
    border-bottom: none;
    border-top-left-radius: 6px;
    border-top-right-radius: 6px;
    margin-right: 2px;
}}
QTabBar::tab:selected {{
    background: {ACCENT};
    color: #07101f;
    font-weight: 600;
}}
QTabBar::tab:hover:!selected {{
    background: #1f2738;
    color: #e6e9ef;
}}
QPushButton {{
    background-color: #1f2738;
    border: 1px solid #313c52;
    border-radius: 6px;
    padding: 6px 14px;
}}
QPushButton:hover {{
    background-color: #28324a;
    border-color: {ACCENT};
}}
QPushButton:pressed {{
    background-color: {ACCENT};
    color: #07101f;
}}
QLineEdit, QDoubleSpinBox, QComboBox, QTreeWidget {{
    background-color: #0e1219;
    border: 1px solid #313c52;
    border-radius: 5px;
    padding: 4px 6px;
    selection-background-color: {ACCENT};
}}
QComboBox QAbstractItemView {{
    background-color: #161b27;
    selection-background-color: {ACCENT};
    border: 1px solid #313c52;
}}
QSlider::groove:horizontal {{
    height: 5px;
    background: #283042;
    border-radius: 3px;
}}
QSlider::handle:horizontal {{
    background: {ACCENT};
    width: 15px;
    margin: -6px 0;
    border-radius: 7px;
}}
QCheckBox::indicator {{
    width: 15px; height: 15px;
    border: 1px solid #3a4760;
    border-radius: 3px;
    background: #0e1219;
}}
QCheckBox::indicator:checked {{
    background: {ACCENT};
    border-color: {ACCENT};
}}
QHeaderView::section {{
    background-color: #1f2738;
    color: #cfd6e4;
    border: none;
    padding: 5px;
}}
QScrollBar:vertical {{
    background: #11151f; width: 11px; margin: 0;
}}
QScrollBar::handle:vertical {{
    background: #313c52; border-radius: 5px; min-height: 24px;
}}
QScrollBar::add-line, QScrollBar::sub-line {{ height: 0; }}
QLineEdit:disabled, QDoubleSpinBox:disabled, QComboBox:disabled {{
    color: #5b6474;
    background-color: #12161f;
    border-color: #232b3c;
}}
QPushButton:disabled {{
    color: #5b6474;
    background-color: #161b27;
    border-color: #232b3c;
}}
QMenu {{
    background-color: #161b27;
    border: 1px solid #313c52;
    border-radius: 6px;
    padding: 4px;
}}
QMenu::item {{
    padding: 5px 22px 5px 12px;
    border-radius: 4px;
}}
QMenu::item:selected {{
    background-color: {ACCENT};
    color: #07101f;
}}
QMessageBox, QDialog QLabel {{
    background-color: transparent;
}}
QSplitter::handle {{
    background-color: #1a2030;
}}
QSplitter::handle:hover {{
    background-color: {ACCENT};
}}
"""
