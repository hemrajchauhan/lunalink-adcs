from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QFormLayout, QLabel, QGroupBox,
    QComboBox, QPushButton, QMessageBox, QScrollArea,
)
from PyQt6.QtCore import Qt, pyqtSignal

from ....simulation.repositories.satellite_repository import SatelliteRepository
from ....simulation.repositories.mission_repository import MissionRepository
from ...dialogs.add_mission_dialog import AddMissionDialog
from ..mission_info_panel import MissionInfoPanel


class MissionTab(QWidget):
    """Choose a mission and launch its ADCS simulation. The selection sits at
    the top; the read-only mission details (orbit, spacecraft sizing,
    simulation settings) follow below in the same scrollable column."""

    simulateRequested = pyqtSignal(str)   # mission name
    missionChanged = pyqtSignal(str)      # mission name

    def __init__(self, parent=None):
        super().__init__(parent)
        self._build_ui()
        self._reload_missions()

    def _build_ui(self):
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)

        # One scrollable column: Selected Mission on top, details below.
        content = QWidget()
        layout = QVBoxLayout(content)
        layout.setSpacing(8)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QScrollArea.Shape.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setWidget(content)
        outer.addWidget(scroll)

        sel = QGroupBox("Selected Mission")
        sform = QFormLayout(sel)

        self.mission_combo = QComboBox()
        self.mission_combo.setToolTip("Choose which mission to view and simulate.")
        self.mission_combo.currentTextChanged.connect(self._update)
        sform.addRow("Mission", self.mission_combo)

        self.desc_label = QLabel("Not selected")
        self.desc_label.setWordWrap(True)
        self.desc_label.setToolTip("What this mission is about.")
        sform.addRow("Description", self.desc_label)

        self.sat_label = QLabel("Not selected")
        self.sat_label.setToolTip("The spacecraft flown on this mission.")
        sform.addRow("Spacecraft", self.sat_label)

        self.parent_label = QLabel("Not selected")
        self.parent_label.setToolTip("The body the spacecraft orbits.")
        sform.addRow("Orbits", self.parent_label)

        buttons = QHBoxLayout()
        self.add_button = QPushButton("Add Mission")
        self.add_button.setToolTip("Create a new mission.")
        self.add_button.clicked.connect(self._add_mission)
        self.delete_button = QPushButton("Delete Mission")
        self.delete_button.setToolTip("Remove the selected mission.")
        self.delete_button.clicked.connect(self._delete_mission)
        buttons.addWidget(self.add_button)
        buttons.addWidget(self.delete_button)
        sform.addRow(buttons)
        layout.addWidget(sel)

        self.run_button = QPushButton("Run ADCS Simulation")
        self.run_button.setToolTip("Run the attitude simulation for this mission "
                                   "and show the results in the plots.")
        self.run_button.clicked.connect(self._run)
        layout.addWidget(self.run_button)

        # Read-only mission details, following the selection above.
        self.info_panel = MissionInfoPanel()
        layout.addWidget(self.info_panel)

        layout.addStretch()

    # ------------------------------------------------------------------
    def showEvent(self, event):
        self._reload_missions()
        super().showEvent(event)

    def _reload_missions(self):
        current = self.mission_combo.currentText()
        names = [m.name for m in MissionRepository().load_all()]
        self.mission_combo.blockSignals(True)
        self.mission_combo.clear()
        self.mission_combo.addItems(names)
        if current in names:
            self.mission_combo.setCurrentText(current)
        self.mission_combo.blockSignals(False)
        self._update(self.mission_combo.currentText())

    def _update(self, name):
        mission = MissionRepository().get_by_name(name) if name else None
        if mission is None:
            self.sat_label.setText("Not selected")
            self.desc_label.setText("Not selected")
            self.parent_label.setText("Not selected")
            self.missionChanged.emit("")
            return
        sat = SatelliteRepository().get_by_name(mission.satellite)
        self.desc_label.setText(mission.description or "No description")
        self.sat_label.setText(mission.satellite)
        self.parent_label.setText((sat.parent if sat else None) or "Unknown")
        self.info_panel.update_for_mission(name)
        self.missionChanged.emit(name)

    def _add_mission(self):
        dialog = AddMissionDialog(self)
        if dialog.exec():
            MissionRepository().add_mission(dialog.build_mission())
            self._reload_missions()
            self.mission_combo.setCurrentText(dialog.name_edit.text().strip())

    def _delete_mission(self):
        name = self.mission_combo.currentText()
        if not name:
            return
        if QMessageBox.question(self, "Delete mission", f"Delete '{name}'?") \
                == QMessageBox.StandardButton.Yes:
            MissionRepository().delete_mission(name)
            self._reload_missions()

    def _run(self):
        name = self.mission_combo.currentText()
        if name:
            self.simulateRequested.emit(name)

    def current_mission(self) -> str:
        return self.mission_combo.currentText()
