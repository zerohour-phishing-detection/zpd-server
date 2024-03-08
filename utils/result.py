import json
from enum import Enum


class ResultTypes(Enum):
    PROCESSING = -2
    LEGITIMATE = -1
    INCONCLUSIVE = 0
    PHISHING = 1

    # DEPRECATED
    @staticmethod
    def to_old(result: "ResultTypes"):
        if result == ResultTypes.PROCESSING:
            return "processing"
        if result == ResultTypes.LEGITIMATE:
            return "not phishing"
        if result == ResultTypes.INCONCLUSIVE:
            return "inconclusive"
        if result == ResultTypes.PHISHING:
            return "phishing"
        raise ValueError("Unknown result type")


# TODO overlaps with State in sessions.py, merge them or sth
class DetectionResult:
    url: str
    url_hash: str

    result: ResultTypes
    status: str

    def __init__(self, url: str, url_hash: str, status: str, result: ResultTypes):
        self.url = url
        self.url_hash = url_hash
        self.status = status
        self.result = result

    def to_json_str(self):
        # TODO rename status to phase (over the whole codebase)
        obj = {
            "url": self.url,
            "status": self.status,
            "result": self.result.name,
            "hash": self.url_hash,
        }

        return json.dumps(obj)

    # DEPRECATED
    def to_json_str_old(self):
        old_result = ResultTypes.to_old(self.result)
        obj = [{"url": self.url, "status": old_result, "sha1": self.url_hash}]
        return json.dumps(obj)
