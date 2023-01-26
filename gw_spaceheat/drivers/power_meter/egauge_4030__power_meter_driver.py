from typing import Optional

from drivers.power_meter.power_meter_driver import PowerMeterDriver


class EGuage4030_PowerMeterDriver(PowerMeterDriver):

    def start(self):
        pass

    def read_current_rms_micro_amps(self) -> int:
        return 0

    def read_hw_uid(self) -> Optional[str]:
        return ""

    def read_power_w(self) -> Optional[int]:
        pass