from enum import Enum

from flask import jsonify


class ResultTypes(Enum):
    PROCESSING = -2
    LEGITIMATE = -1
    INCONCLUSIVE = 0
    PHISHING = 1

    @classmethod
    def to_old(cls, result: "ResultTypes"):
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

    result: str
    status: str

    def __init__(self, url: str, url_hash: str, status: str, result: ResultTypes):
        self.url : str = url
        self.url_hash : str = url_hash
        self.status : str = status
        self.result : ResultTypes = result

    def to_json_str(self):
        # TODO rename status to phase (over the whole codebase)
        obj = [
            {"url": self.url, "status": self.status, "result": self.result.name, "hash": self.url_hash}
        ]
        return jsonify(obj)

    # DEPRECATED
    def to_json_str_old(self):
        old_result = ResultTypes.to_old(self.result)
        obj = [{"url": self.url, "status": old_result, "sha1": self.url_hash}]
        return jsonify(obj)
