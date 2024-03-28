import json
import sqlite3
from datetime import datetime

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
            obj = {"error": "There are no saved settings for the given UUID!"}
            return obj

        settings_json = json.loads(settings_string)
        return settings_json

    def set_settings(self, uuid: str, settings_json: object) -> object:
        storage_conn = sqlite3.connect(self.db_path)

        timestamp = datetime.now()
        settings_str = json.dumps(settings_json)

        obj = {}

        try:
            if self._get_settings(uuid) is None:
                storage_conn.execute(
                    "INSERT INTO settings (uuid, settings, timestamp) VALUES (?, ?, ?)",
                    [uuid, settings_str, timestamp],
                )
                obj = {"result": "Succesfuly saved the settings to the server's database!"}

            else:
                storage_conn.execute(
                    "UPDATE settings SET settings = ?, timestamp = ? WHERE uuid = ?",
                    [settings_str, timestamp, uuid],
                )
                obj = {"result": "Succesfuly updated the settings!"}

        except Exception as e:
            obj = {"error": f"An error occured while saving the settings: {e}"}

        storage_conn.commit()
        storage_conn.close()

        return obj
