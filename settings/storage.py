import json
import sqlite3
from datetime import datetime

from settings.detection import DetectionSettings
from utils.logging import main_logger

logger = main_logger.getChild("settings.storage")


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
        # storage_conn.commit()
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

        if not DetectionSettings.verify(settings_json):
            return False

        ok = True

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

        # storage_conn.commit()
        storage_conn.close()

        return ok
