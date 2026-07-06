import datetime
import math

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QFormLayout, QGroupBox, QSlider, QPushButton,
    QCheckBox, QLabel,
)
from PyQt6.QtCore import Qt

from ....config import TIME_ACCEL_MIN, TIME_ACCEL_MAX, TIME_ACCELERATION

# J2000 epoch (2000-01-01 12:00 UTC), used to place the model at "today".
_J2000 = datetime.datetime(2000, 1, 1, 12, 0, 0, tzinfo=datetime.timezone.utc)


class VisualizationTab(QWidget):

    SLIDER_STEPS = 1000

    def __init__(self, scene_manager, parent=None):
        super().__init__(parent)
        self.scene_manager = scene_manager
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)

        playback = QGroupBox("Playback")
        form = QFormLayout(playback)

        self.play_button = QPushButton("⏸ Pause")
        self.play_button.clicked.connect(self._toggle_play)

        self.speed_slider = QSlider(Qt.Orientation.Horizontal)
        self.speed_slider.setRange(0, self.SLIDER_STEPS)
        self.speed_slider.setValue(self._accel_to_slider(TIME_ACCELERATION))
        self.speed_slider.valueChanged.connect(self._on_speed)

        self.speed_label = QLabel()
        self._update_speed_label(TIME_ACCELERATION)

        self.realtime_check = QCheckBox("Real-time (1×)")
        self.realtime_check.toggled.connect(self._on_realtime)

        self.epoch_button = QPushButton("Reset to present day")
        self.epoch_button.setToolTip(
            "Place the planets at their positions for the current date and pause.")
        self.epoch_button.clicked.connect(self._go_to_today)

        form.addRow(self.play_button)
        form.addRow("Speed", self.speed_slider)
        form.addRow("", self.speed_label)
        form.addRow("", self.realtime_check)
        form.addRow("", self.epoch_button)
        layout.addWidget(playback)

        inspect = QGroupBox("Inspect an Object")
        ilayout = QVBoxLayout(inspect)
        tip = QLabel("Open the Objects tab and double-click any object to centre "
                     "the camera on it and view its details.")
        tip.setWordWrap(True)
        ilayout.addWidget(tip)
        layout.addWidget(inspect)

        view = QGroupBox("Scene")
        vform = QVBoxLayout(view)
        self.labels_check = QCheckBox("Show object names")
        self.labels_check.setToolTip("Show or hide the text labels next to each body.")
        self.labels_check.setChecked(True)
        self.labels_check.toggled.connect(self.scene_manager.set_labels_visible)
        self.orbits_check = QCheckBox("Show orbit paths")
        self.orbits_check.setToolTip("Show or hide the orbit trace lines.")
        self.orbits_check.setChecked(True)
        self.orbits_check.toggled.connect(self.scene_manager.set_orbits_visible)
        vform.addWidget(self.labels_check)
        vform.addWidget(self.orbits_check)
        layout.addWidget(view)

        layout.addStretch()

    # -- logarithmic speed slider -----------------------------------------
    def _slider_to_accel(self, value: int) -> float:
        frac = value / self.SLIDER_STEPS
        return TIME_ACCEL_MIN * (TIME_ACCEL_MAX / TIME_ACCEL_MIN) ** frac

    def _accel_to_slider(self, accel: float) -> int:
        frac = math.log(accel / TIME_ACCEL_MIN) / math.log(TIME_ACCEL_MAX / TIME_ACCEL_MIN)
        return int(round(frac * self.SLIDER_STEPS))

    def _update_speed_label(self, accel: float):
        if accel < 120:
            self.speed_label.setText(f"{accel:.0f}×  (~real-time)")
        elif accel < 86400:
            self.speed_label.setText(f"{accel / 3600:.1f} sim-hours / sec")
        else:
            self.speed_label.setText(f"{accel / 86400:.1f} sim-days / sec")

    def _on_speed(self, value):
        accel = self._slider_to_accel(value)
        self.scene_manager.set_time_acceleration(accel)
        self._update_speed_label(accel)
        if self.realtime_check.isChecked():
            self.realtime_check.blockSignals(True)
            self.realtime_check.setChecked(False)
            self.realtime_check.blockSignals(False)

    def _on_realtime(self, checked):
        if checked:
            self.scene_manager.set_time_acceleration(1.0)
            self._update_speed_label(1.0)
        else:
            self._on_speed(self.speed_slider.value())

    def _toggle_play(self):
        running = self.scene_manager.toggle_animation()
        self.play_button.setText("⏸ Pause" if running else "▶ Play")

    def _go_to_today(self):
        now = datetime.datetime.now(datetime.timezone.utc)
        seconds_since_j2000 = (now - _J2000).total_seconds()
        self.scene_manager.freeze_at_time(seconds_since_j2000)
        self.play_button.setText("▶ Play")
