import json
import sqlite3
from datetime import datetime

from registry import DECISION_STRATEGIES, DETECTION_METHODS
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
    def from_json(settings_json: object) -> "DetectionSettings":
        detection_methods = settings_json["detection_methods"]

        decision_strategy = settings_json["decision_strategy"]

        if "bypass_cache" in settings_json:
            bypass_cache = settings_json["bypass_cache"]
            return DetectionSettings(detection_methods, decision_strategy, bypass_cache)

        return DetectionSettings(detection_methods, decision_strategy)

    @staticmethod
    def verify_json(settings_json: object) -> bool:
        if "detection_methods" not in settings_json:
            return False

        if "decision_strategy" not in settings_json:
            return False

        for methods in settings_json["detection_methods"]:
            if methods not in DETECTION_METHODS:
                return False

        if settings_json["decision_strategy"] not in DECISION_STRATEGIES:
            return False

        return True


class SettingsStorage:
    db_path: str

    def __init__(self, db_path: str):
        self.db_path = db_path
        storage_conn = sqlite3.connect(self.db_path)
        self._setup_storage(storage_conn)

    def _setup_storage(self, storage_conn):
        sql_q_db = """
            CREATE TABLE IF NOT EXISTS "settings" (
                "uuid"	string,
                "settings" string,
                "timestamp" string
            );"""

        storage_conn.execute(sql_q_db)
        storage_conn.commit()
        storage_conn.close()

    def _get_settings(self, uuid: str) -> str:
        storage_conn = sqlite3.connect(self.db_path)

        cursor = storage_conn.execute("SELECT settings FROM settings WHERE uuid = ?", [uuid])
        settings = cursor.fetchone()

        storage_conn.close()

        if settings is not None:
            return settings[0]

        return settings

    def get_settings(self, uuid: str) -> object:
        settings_string = self._get_settings(uuid)

        if settings_string is None:
            return

        settings_json = json.loads(settings_string)
        return settings_json

    def set_settings(self, uuid: str, settings_json: object) -> bool:
        storage_conn = sqlite3.connect(self.db_path)

        ok = True

        if not DetectionSettings.verify_json(settings_json):
            logger.error(f"The JSON body sent by {uuid} for the settings is not valid.")
            return False

        try:
            timestamp = datetime.now()
            settings_str = json.dumps(settings_json)
            if self._get_settings(uuid) is None:
                storage_conn.execute(
                    "INSERT INTO settings (uuid, settings, timestamp) VALUES (?, ?, ?)",
                    [uuid, settings_str, timestamp],
                )

            else:
                storage_conn.execute(
                    "UPDATE settings SET settings = ?, timestamp = ? WHERE uuid = ?",
                    [settings_str, timestamp, uuid],
                )

        except Exception as e:
            logger.error(e)
            ok = False
        #     obj = {"error": f"An error occured while saving the settings: {e}"}

        storage_conn.commit()
        storage_conn.close()

        return ok
