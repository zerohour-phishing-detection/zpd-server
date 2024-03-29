from settings import Settings
from settings.dst import DSTSettings


class DetectionSettings(Settings):
    detection_methods: list[str]
    decision_strategy: str
    bypass_cache: bool
    methods_settings: list[Settings]

    def __init__(
        self,
        detection_methods: list[str] = ["dst"],
        decision_strategy: str = "majority",
        bypass_cache: bool = False,
        methods_settings: list[Settings] = [DSTSettings()],
    ):
        self.detection_methods = detection_methods
        self.decision_strategy = decision_strategy
        self.bypass_cache = bypass_cache
        self.methods_settings = methods_settings

    @staticmethod
    def from_json(settings_json: object) -> "DetectionSettings":
        if "detection_methods" not in settings_json:
            return DetectionSettings()
        detection_methods = settings_json["detection_methods"]

        if "decision_strategy" not in settings_json:
            return DetectionSettings(detection_methods)
        decision_strategy = settings_json["decision_strategy"]

        if "bypass_cache" not in settings_json:
            return DetectionSettings(detection_methods, decision_strategy)

        bypass_cache = settings_json["bypass_cache"]
        return DetectionSettings(detection_methods, decision_strategy, bypass_cache)