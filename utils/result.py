from enum import Enum

from flask import jsonify


class ResultTypes(Enum):
    PROCESSING = -2
    LEGITIMATE = -1
    INCONCLUSIVE = 0
    PHISHING = 1
    

# TODO overlaps with State in sessions.py, merge them or sth
class DetectionResult:
    url: str
    url_hash: str

    result : ResultTypes
    status: str

    def __init__(self, url: str, url_hash: str, status: str, result: ResultTypes):
        self.url = url
        self.url_hash = url_hash
        self.status = status
        self.result = result

    def to_json_str(self):
        # TODO return object doesnt need to specify the type of hash (rename to just 'hash' or sth instead of 'sha1')
        obj = [{"url": self.url, "status": self.result, "sha1": self.url_hash}]
        return jsonify(obj)
