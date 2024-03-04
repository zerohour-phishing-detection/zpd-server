import os

import methods.reverse_image_search as reverse_image_search
from methods.detection_methods import DetectionMethods
from utils.custom_logger import CustomLogger
from utils.decision import DecisionStrategies
from utils.results import DetectionResult
from utils.sessions import SessionStorage

# Option for saving the taken screenshots
SAVE_SCREENSHOT_FILES = False
# Whether to use the Clearbit logo API (see https://clearbit.com/logo)
USE_CLEARBIT_LOGO_API = True

# Where to store temporary session files, such as screenshots
SESSION_FILE_STORAGE_PATH = "files/"
# Database path for the operational output (?)
DB_PATH_OUTPUT = "db/output_operational.db"
# Database path for the sessions
DB_PATH_SESSIONS = "db/sessions.db"
if not os.path.isdir("db"):
    os.mkdir("db")

# The storage interface for the sessions
session_storage = SessionStorage(DB_PATH_SESSIONS, False)

# The main logger for the whole program, singleton
main_logger = CustomLogger().main_logger


def test(data: "DetectionData") -> "DetectionResult":
    return reverse_image_search.test(data.url, data.screenshot_url, data.uuid, data.pagetitle, "")


def test_new(data: "DetectionData", settings: "DetectionSettings") -> "DetectionResult":
    results = []

    for method in settings.methods:
        print(method)
        if method == DetectionMethods.ReverseImageSearch:
            results.append(
                reverse_image_search.test(
                    data.url, data.screenshot_url, data.uuid, data.pagetitle, ""
                )
            )
        else:
            main_logger.error(f"Method {method} not implemented yet.")

    return DetectionResult(
        data.url, DecisionStrategies.decide(settings.decision_strategy, results[0].url_hash)
    )


class DetectionSettings:
    methods: list[DetectionMethods]
    engines: list[str]  # in order of priority
    # decision_strategy: list[DecisionStrategies]

    def __init__(
        self,
        methods: list[DetectionMethods],
        engines: list[str],
        # decision_strategy: list[DecisionStrategies],
    ):
        self.methods = methods
        self.engines = engines
        # self.decision_strategy = decision_strategy

    @classmethod
    def from_json(cls, json):
        # TODO: find a better way to do this
        raw = json["methods"]
        cls.methods = [
            DetectionMethods[method] for method in raw if method in DetectionMethods.__members__
        ]
        cls.engines = json["engines"]
        # cls.decision_strategy = json["decision_strategy"]

        return cls


class DetectionData:
    url: str
    screenshot_url: str
    uuid: str
    pagetitle: str

    def __init__(
        self, url: str = "", screenshot_url: str = "", uuid: str = "", pagetitle: str = ""
    ):
        self.url = url
        self.screenshot_url = screenshot_url
        self.uuid = uuid
        self.pagetitle = pagetitle

    @classmethod
    def from_json(cls, json):
        cls.url = json["URL"]
        cls.screenshot_url = json["URL"]

        # extra json field for evaluation purposes
        # the hash computed in the DB is the this one
        if "phishURL" in json:  # TODO: only allow this on a testing environment, not prod
            cls.url = json["phishURL"]
            main_logger.info(f"Real URL changed to phishURL: {cls.url}\n")

        cls.pagetitle = json["pagetitle"]
        cls.uuid = json["uuid"]

        return cls
