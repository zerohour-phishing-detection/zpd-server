import os
from enum import Enum

from flask import jsonify

from utils.custom_logger import CustomLogger
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

def test(url, screenshot_url, uuid, pagetitle, image64) -> "DetectionResult":
    main_logger.info(f"""

##########################################################
##### Request received for URL:\t{url}
##########################################################
""")


class DetectionData:
    url: str
    screenshot_url: str
    uuid: str
    image64: str
    
    def __init__(self, url: str, screenshot_url: str, uuid: str, image64: str):
        self.url = url
        self.screenshot_url = screenshot_url
        self.uuid = uuid
        self.image64 = image64


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
