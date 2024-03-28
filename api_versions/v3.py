from flask import Blueprint, jsonify, request

import detection
from detection import DetectionData
from utils.logging import main_logger
from utils.registry import DECISION_STRATEGIES, DETECTION_METHODS

# Instantiate a logger for this version of the API
logger = main_logger.getChild("api.v3")

# Create a blueprint for this version of the API
v3 = Blueprint("v3", import_name="v3")

# The storage interface for the sessions
session_storage = detection.session_storage

# The storage interface for the settings per user
settings_storage = detection.settings_storage


@v3.route("/check", methods=["POST"])
def check():
    uuid = request.cookies.get("uuid")
    json = request.get_json()
    data = DetectionData.from_json(json)

    return detection.check(uuid, data).to_json_str()


@v3.route("/state", methods=["POST"])
def get_state():
    uuid = request.cookies.get("uuid")
    json = request.get_json()
    url = json["url"]

    session = session_storage.get_session(uuid, url)
    status = session.get_state()

    if status is None:
        return jsonify({"error": "No session found for this URL and UUID combination."})

    result = [{"result": status.result, "state": status.state}]

    return jsonify(result)


@v3.route("/settings", methods=["GET"])
def get_settings():
    uuid = request.cookies.get("uuid")
    return settings_storage.get_settings(uuid)


@v3.route("/settings", methods=["POST"])
def set_settings():
    uuid = request.cookies.get("uuid")
    json = request.get_json()
    return settings_storage.set_settings(uuid, json)


@v3.route("/capabilities", methods=["GET"])
def get_available_capabilities():
    uuid = request.cookies.get("uuid")

    logger.info(f"Capabilites request from uuid: {uuid}")
    result = {
        "detection_methods": list(DETECTION_METHODS.keys()),
        "decision_strategies": list(DECISION_STRATEGIES.keys()),
    }
    return jsonify(result)
