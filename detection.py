import hashlib
import os

from methods.detection_methods import DetectionMethods
from utils.custom_logger import CustomLogger
from utils.decision import DECISION_STRATEGIES
from utils.result import DetectionResult, ResultType
from utils.sessions import SessionStorage
from utils.timing import TimeIt

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
def test_old(data: "DetectionData") -> "DetectionResult":
    return test(
        data, DetectionSettings()
    )


def test(data: "DetectionData", settings: "DetectionSettings") -> "DetectionResult":
    main_logger.info(f"""

##########################################################
##### Request received for URL:\t{data.url}
##########################################################
""")
    url_hash = hashlib.sha256(data.url.encode("utf-8")).hexdigest()
    session = session_storage.get_session(data.uuid, data.url)

    if not settings.bypass_cache:
        with TimeIt("cache check"):
            # Check if URL is in cache or still processing
            cache_result = session.get_state()

            if cache_result is not None:
                main_logger.info(
                    f"[STATE] {cache_result.state} [RESULT] {cache_result.result}, for url {data.url}, served from cache"
                )

                return DetectionResult(
                    data.url, url_hash, cache_result.state, ResultType[cache_result.result]
                )

    # Update the current state in the session storage
    session.set_state(ResultType.PROCESSING.name, "STARTED")

    results = []

    for method in settings.detection_methods:
        main_logger.info(f"Started running method {method.name}")
        results.append(
            method.value.run(data.url, data.screenshot_url, data.uuid, data.pagetitle, None)
        )

    result = DECISION_STRATEGIES[settings.decision_strategy].decide(settings.decision_strategy, results)
    session.set_state(result.name, "DONE")

    return DetectionResult(data.url, url_hash, "DONE", result)


class DetectionSettings:
    detection_methods: list[DetectionMethods]
    decision_strategy: str
    bypass_cache: bool

    def __init__(
        self,
        detection_methods: list[DetectionMethods] = [DetectionMethods.ReverseImageSearch],
        decision_strategy: str = "Majority",
        bypass_cache: bool = False,
    ):
        self.detection_methods = detection_methods
        self.decision_strategy = decision_strategy
        self.bypass_cache = bypass_cache

    @staticmethod
    def from_json(json):
        detection_methods = json["detection-methods"]

        decision_strategy = json["decision-strategy"]

        
        if "bypass-cache" in json:
            bypass_cache = json["bypass-cache"]
            return DetectionSettings(detection_methods, decision_strategy, bypass_cache)

        return DetectionSettings(detection_methods, decision_strategy)


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

    @staticmethod
    def from_json(json):
        url = json["URL"]
        screenshot_url = json["URL"]

        # extra json field for evaluation purposes
        # the hash computed in the DB is the this one
        if "phishURL" in json:  # TODO: only allow this on a testing environment, not prod
            url = json["phishURL"]
            main_logger.info(f"Real URL changed to phishURL: {url}\n")

        pagetitle = json["pagetitle"]
        uuid = json["uuid"]

        return DetectionData(url, screenshot_url, uuid, pagetitle)
