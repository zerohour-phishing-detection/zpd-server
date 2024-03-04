import os

import methods.reverse_image_search as reverse_image_search
from methods.detection_methods import DetectionMethods
from utils.custom_logger import CustomLogger
from utils.decision import DecisionStrategies
from utils.result import DetectionResult
from utils.sessions import SessionStorage

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


# DEPRECATED
def test(data: "DetectionData") -> "DetectionResult":
    main_logger.info(f"""

##########################################################
##### [DEPRECATED] Request received for URL:\t{data.url}
##########################################################
""")

    return reverse_image_search.test(data.url, data.screenshot_url, data.uuid, data.pagetitle, "")


def test_new(data: "DetectionData", settings: "DetectionSettings") -> "DetectionResult":
    main_logger.info(f"""

##########################################################
##### Request received for URL:\t{data.url}
##########################################################
""")

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
        data.url,
        DecisionStrategies.decide(settings.decision_strategy, results),
        results[0].hash_url,
    )


class DetectionSettings:
    detection_methods: list[DetectionMethods]
    decision_strategy: list[DecisionStrategies]

    def __init__(
        self,
        detection_methods: list[DetectionMethods],
        decision_strategy: list[DecisionStrategies],
    ):
        self.detection_methods = detection_methods
        self.decision_strategy = decision_strategy

    @classmethod
    def from_json(cls, json):
        cls.detection_methods = [
            DetectionMethods[method]
            for method in json["detection-methods"]
            if method in DetectionMethods.__members__
        ]
        
        cls.decision_strategy = json["decision-strategy"]

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
