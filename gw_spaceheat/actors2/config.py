from proactor import ProactorSettings

class ScadaSettings(ProactorSettings):
    """Settings for the GridWorks scada."""
    seconds_per_report: int = 300
    async_power_reporting_threshold = 0.02

    class Config(ProactorSettings.Config):
        env_prefix = "SCADA_"
