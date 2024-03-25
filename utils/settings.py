import sqlite3

from utils.logging import main_logger

logger = main_logger.getChild("utils.settings")


class DetectionSettings:
    detection_methods: list[str]
    decision_strategy: str
    bypass_cache: bool

    def __init__(
        self,
        detection_methods: list[str] = ["dst"],
        decision_strategy: str = "majority",
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
    def from_json(json) -> "DetectionData":
        url = json["URL"]
        screenshot_url = json["URL"]

        # extra json field for evaluation purposes
        # the hash computed in the DB is the this one
        if "phishURL" in json:  # TODO: only allow this on a testing environment, not prod
            url = json["phishURL"]
            logger.info(f"Real URL changed to phishURL: {url}\n")

        pagetitle = json["pagetitle"]
        uuid = json["uuid"]

        return DetectionData(url, screenshot_url, uuid, pagetitle)


class SettingsStorage:
    def __init__(self, db_path: str):
        storage_conn = sqlite3.connect(db_path)
        self._setup_storage(storage_conn)

    def _setup_storage(self, storage_conn):
        sql_q_db = """
            CREATE TABLE IF NOT EXISTS "settings" (
                "uuid"	string,
                "settings" string
            );"""

        storage_conn.execute(sql_q_db)
        storage_conn.commit()

    # def set_settings(uuid: str, settings: DetectionSettings):
