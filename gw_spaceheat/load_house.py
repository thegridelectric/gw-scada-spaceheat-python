
from actors2.config import ScadaSettings
from data_classes.hardware_layout import HardwareLayout


def load_all(settings: ScadaSettings) -> HardwareLayout:
    return HardwareLayout.load(settings.paths.hardware_layout)

