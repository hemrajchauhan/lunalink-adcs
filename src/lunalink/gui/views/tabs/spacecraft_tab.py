from PyQt6.QtWidgets import QWidget, QFormLayout, QLabel, QVBoxLayout, QGroupBox

from ....simulation.adcs import box_inertia, sizing_summary, ADCSParams
from ....simulation.repositories.satellite_repository import SatelliteRepository


class SpacecraftTab(QWidget):
    """Mass properties and actuator-sizing summary for the spacecraft."""

    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)

        sat = SatelliteRepository().get_by_name("LunaLink")
        mass = sat.mass_kg if sat else 500.0
        dims = tuple(sat.dimensions_m) if sat else (2.0, 1.5, 1.0)
        I = box_inertia(mass, dims)

        props = QGroupBox("Mass properties (uniform box)")
        form = QFormLayout(props)
        form.addRow("Mass", QLabel(f"{mass:.0f} kg"))
        form.addRow("Envelope", QLabel(f"{dims[0]} × {dims[1]} × {dims[2]} m"))
        form.addRow("Inertia Ix", QLabel(f"{I[0]:.1f} kg·m²"))
        form.addRow("Inertia Iy", QLabel(f"{I[1]:.1f} kg·m²"))
        form.addRow("Inertia Iz", QLabel(f"{I[2]:.1f} kg·m²"))
        layout.addWidget(props)

        sizing = sizing_summary(ADCSParams(mass_kg=mass, dims_m=dims))
        box = QGroupBox("Actuator sizing (hand-calc)")
        sform = QFormLayout(box)
        sform.addRow("Slew torque (90°/5 min)", QLabel(f"{sizing['slew_torque_nm']*1000:.1f} mN·m"))
        sform.addRow("Slew momentum", QLabel(f"{sizing['slew_momentum_nms']:.2f} N·m·s"))
        sform.addRow("Cyclic storage", QLabel(f"{sizing['cyclic_storage_nms']:.3f} N·m·s"))
        sform.addRow("Recommended wheel hmax", QLabel(f"{sizing['recommended_wheel_hmax_nms']:.1f} N·m·s"))
        layout.addWidget(box)
        layout.addStretch()
