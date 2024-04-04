import uuid

from flask import Blueprint, g, jsonify, request

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


@v3.before_request
def before_request():
    g.uuid = request.cookies.get("uuid")

    if g.uuid is None:
        g.uuid = str(uuid.uuid4())
        logger.info(f"Generating new uuid: {g.uuid}")


@v3.after_request
def after_request(response):
    if request.cookies.get("uuid") is None:
        response.set_cookie("uuid", g.uuid)

    return response

@v3.route("/ping", methods=["GET"])
def ping():
    return ""


# TODO: Use jsonify instead for consistency
@v3.route("/check", methods=["POST"])
def check():
    json = request.get_json()
    data = DetectionData.from_json(json)

    return detection.check(g.uuid, data).to_json_str()


@v3.route("/state", methods=["POST"])
def get_state():
    json = request.get_json()
    url = json["url"]

    session = session_storage.get_session(g.uuid, url)
    status = session.get_state()

    if status is None:
        return ("", 404)

    result = {"result": status.result, "state": status.state}

    return jsonify(result)


@v3.route("/settings", methods=["GET"])
def get_settings():
    settings = settings_storage.get_settings(g.uuid)

    if settings is None:
        return ("", 404)

    return jsonify(settings)


@v3.route("/settings", methods=["POST"])
def set_settings():
    json = request.get_json()

    if not settings_storage.set_settings(g.uuid, json):
        return ("", 400)

    return ("", 200)


@v3.route("/capabilities", methods=["GET"])
def get_available_capabilities():

    logger.info(f"Capabilites request from uuid: {g.uuid}")
    result = {
        "detection_methods": list(DETECTION_METHODS.keys()),
        "decision_strategies": list(DECISION_STRATEGIES.keys()),
    }
    return jsonify(result)
