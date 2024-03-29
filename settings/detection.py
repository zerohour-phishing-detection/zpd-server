from registry import DETECTION_METHODS_SETTINGS
from settings import Settings


class DetectionSettings(Settings):
    detection_methods: list[str]
    decision_strategy: str
    bypass_cache: bool
    methods_settings: dict[str, Settings]

    def __init__(
        self,
        detection_methods: list[str] = ["dst"],
        decision_strategy: str = "majority",
        bypass_cache: bool = False,
        methods_settings: dict[str, Settings] = DETECTION_METHODS_SETTINGS,
    ):
        self.detection_methods = detection_methods
        self.decision_strategy = decision_strategy
        self.bypass_cache = bypass_cache
        self.methods_settings = methods_settings

    @staticmethod
    def from_json(settings_json: object) -> "DetectionSettings":
        detection_methods = settings_json["detection_methods"]

        decision_strategy = settings_json["decision_strategy"]

        methods_settings = dict()
        for method in detection_methods:
            if method not in settings_json:
                methods_settings.update({method: DETECTION_METHODS_SETTINGS[method]})
                continue
            else:
                methods_settings.update({
                    method: DETECTION_METHODS_SETTINGS[method].from_json(settings_json[method])
                })

        if "bypass_cache" in settings_json:
            bypass_cache = settings_json["bypass_cache"]
            return DetectionSettings(detection_methods, decision_strategy, methods_settings)

        return DetectionSettings(
            detection_methods, decision_strategy, methods_settings, bypass_cache
        )
