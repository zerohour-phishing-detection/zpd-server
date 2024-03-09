from flask import Blueprint, request

import detection
from detection import DetectionData, DetectionSettings
from utils.logging import main_logger

# Instantiate a logger for this version of the API
logger = main_logger.getChild("v2")

# Create a blueprint for this version of the API
v2 = Blueprint("v2", import_name="v2")


@v2.route("/url", methods=["POST"])
def check_url():
    json = request.get_json()
    json_data = json["data"]
    json_settings = json["settings"]

    res = detection.test(
        DetectionData.from_json(json_data), DetectionSettings.from_json(json_settings)
    )

    return res.to_json_str()