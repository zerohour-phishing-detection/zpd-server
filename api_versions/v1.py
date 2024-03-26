from flask import Blueprint, jsonify, request

import detection
from detection import DetectionData
from utils.logging import main_logger

# Instantiate a logger for this version of the API
logger = main_logger.getChild("api.v1")

# Create a blueprint for this version of the API
v1 = Blueprint("v1", import_name="v1")

# The storage interface for the sessions
session_storage = detection.session_storage


@v1.route("/url", methods=["POST"])
def check_url_old():
    json = request.get_json()

    res = detection.check(DetectionData.from_json(json))

    return res.to_json_str_old()


@v1.route("/url/state", methods=["POST"])
def get_url_state():
    json = request.get_json()
    url = json["URL"]
    uuid = json["uuid"]

    session = session_storage.get_session(uuid, url)
    status = session.get_state()

    result = [{"status": status.result, "state": status.state}]

    return jsonify(result)
