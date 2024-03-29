from registry import DECISION_STRATEGIES, DETECTION_METHODS, DETECTION_METHODS_SETTINGS
from settings import Settings
from utils.logging import main_logger

logger = main_logger.getChild("settings.detection")


class DetectionSettings(Settings):
    detection_methods: list[str]
    decision_strategy: str
    bypass_cache: bool
    methods_settings: dict[str, Settings]

    def __init__(
        self,
        detection_methods: list[str] = ["dst"],
        decision_strategy: str = "majority",
        methods_settings: dict[str, Settings] = DETECTION_METHODS_SETTINGS,
        bypass_cache: bool = False,
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
            return DetectionSettings(
                detection_methods, decision_strategy, methods_settings, bypass_cache
            )

        return DetectionSettings(detection_methods, decision_strategy, methods_settings)

    @staticmethod
    def verify(settings_json: object) -> bool:
        try:
            detection_methods = settings_json["detection_methods"]
            decision_strategy = settings_json["decision_strategy"]

            for methods in detection_methods:
                DETECTION_METHODS[methods]

            DECISION_STRATEGIES[decision_strategy]

        except Exception:
            return False

        return True
