from flask import Blueprint, jsonify, request

import detection
from detection import DetectionData
from registry import DECISION_STRATEGIES, DETECTION_METHODS
from utils.logging import main_logger

# Instantiate a logger for this version of the API
logger = main_logger.getChild("api.v3")

# Create a blueprint for this version of the API
v3 = Blueprint("v3", import_name="v3")

# The storage interface for the sessions
session_storage = detection.session_storage

# The storage interface for the settings per user
settings_storage = detection.settings_storage


@v3.route("/ping", methods=["GET"])
def ping():
    return ""


# TODO: Use jsonify instead for consistency
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
        return ("", 404)

    result = {"result": status.result, "state": status.state}

    return jsonify(result)


@v3.route("/settings", methods=["GET"])
def get_settings():
    uuid = request.cookies.get("uuid")

    settings = settings_storage.get_settings(uuid)

    if settings is None:
        return ("", 404)

    return jsonify(settings_storage.get_settings(uuid))


@v3.route("/settings", methods=["POST"])
def set_settings():
    uuid = request.cookies.get("uuid")
    json = request.get_json()

    if not settings_storage.set_settings(uuid, json):
        return ("", 400)

    return ("", 200)


@v3.route("/capabilities", methods=["GET"])
def get_available_capabilities():
    uuid = request.cookies.get("uuid")

    logger.info(f"Capabilites request from uuid: {uuid}")
    result = {
        "detection_methods": list(DETECTION_METHODS.keys()),
        "decision_strategies": list(DECISION_STRATEGIES.keys()),
    }
    return jsonify(result)