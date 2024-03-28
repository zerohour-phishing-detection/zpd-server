from flask import Blueprint, jsonify, request

import detection
from detection import DetectionData
from utils.logging import main_logger
from utils.registry import DECISION_STRATEGIES, DETECTION_METHODS

# Instantiate a logger for this version of the API
logger = main_logger.getChild("api.v2")

# Create a blueprint for this version of the API
v2 = Blueprint("v2", import_name="v2")

# The storage interface for the sessions
session_storage = detection.session_storage

# The storage interface for the settings per user
settings_storage = detection.settings_storage


@v2.route("/check", methods=["POST"])
def check():
    json = request.get_json()
    uuid = json["uuid"]
    data = DetectionData.from_json(json)

    return detection.check(uuid, data).to_json_str()


@v2.route("/state", methods=["POST"])
def get_state():
    json = request.get_json()
    url = json["URL"]
    uuid = json["uuid"]

    session = session_storage.get_session(uuid, url)
    status = session.get_state()

    result = [{"result": status.result, "state": status.state}]

    return jsonify(result)


@v2.route("/settings", methods=["GET"])
def get_settings():
    json = request.get_json()
    uuid = json["uuid"]
    return jsonify(settings_storage.get_settings(uuid))


@v2.route("/settings", methods=["POST"])
def set_settings():
    json = request.get_json()
    uuid = json["uuid"]
    settings = json["settings"]
    return jsonify(settings_storage.set_settings(uuid, settings))


@v2.route("/capabilities", methods=["GET"])
def get_available_capabilities():
    result = {
        "detection_methods": list(DETECTION_METHODS.keys()),
        "decision_strategies": list(DECISION_STRATEGIES.keys()),
    }
    return jsonify(result)
