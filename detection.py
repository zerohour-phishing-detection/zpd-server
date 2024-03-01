import os
from enum import Enum

from flask import jsonify

import methods.default_method as reverse_image_search
from methods.detection_methods import DetectionMethods
from utils.custom_logger import CustomLogger
from utils.decision_strategy import DecisionStrategies
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
    return reverse_image_search.test(data.url, data.screenshot_url, data.uuid, "", data.image64)

def test_new (data: "DetectionData", settings: "DetectionSettings") -> "DetectionResult":
    
    results = []
    
    for method in settings.methods:
        if method == DetectionMethods.ReverseImageSearch:
            results += reverse_image_search.test(data.url, data.screenshot_url, data.uuid, "", data.image64)
        else:
            main_logger.error(f"Method {method} not implemented yet.")
    
    DecisionStrategies.decide(settings.decision_strategy, results)
      
class DetectionSettings:
    methods: list[DetectionMethods]
    engines: list[str]
    decision_strategy: list[DecisionStrategies]

    def __init__(
        self,
        methods: list[DetectionMethods],
        engines: list[str],
        decision_strategy: list[DecisionStrategies],
    ):
        self.methods = methods
        self.engines = engines
        self.decision_strategy = decision_strategy

    # TODO implement from_json
    @classmethod
    def from_json(cls, json):
        pass


class DetectionData:
    url: str
    screenshot_url: str
    uuid: str
    image64: str

    def __init__(self, url: str = "", screenshot_url: str = "", uuid: str = "", image64: str = ""):
        self.url = url
        self.screenshot_url = screenshot_url
        self.uuid = uuid
        self.image64 = image64

    @classmethod
    def from_json(cls, json):
        cls.url = json["URL"]
        cls.screenshot_url = json["URL"]

        # extra json field for evaluation purposes
        # the hash computed in the DB is the this one
        if "phishURL" in json:  # TODO only allow this on a testing environment, not prod
            cls.url = json["phishURL"]
            main_logger.info(f"Real URL changed to phishURL: {cls.url}\n")

        cls.uuid = json["uuid"]
        cls.image64 = json["image64"]

        return cls


class ResultTypes(Enum):
    LEGITIMATE = -1
    INCONCLUSIVE = 0
    PHISHING = 1

    def __str__(self):
        return self.name


# TODO overlaps with State in sessions.py, merge them or sth
class DetectionResult:
    url: str
    url_hash: str

    status: ResultTypes

    def __init__(self, url: str, url_hash: str, status: str):
        self.url = url
        self.url_hash = url_hash
        self.status = status

    def to_json_str(self):
        # TODO return object doesnt need to specify the type of hash (rename to just 'hash' or sth instead of 'sha1')
        obj = [{"url": self.url, "status": self.status, "sha1": self.url_hash}]
        return jsonify(obj)
