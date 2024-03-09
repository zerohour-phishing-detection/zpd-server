from flask import Blueprint, request

import detection
from detection import DetectionData
from utils.logging import main_logger

# Instantiate a logger for this version of the API
logger = main_logger.getChild("v1")


# Create a blueprint for this version of the API
v1 = Blueprint("v1", import_name="v1")


# DEPRECATED
@v1.route("/url", methods=["POST"])
def check_url_old():
    json = request.get_json()

    res = detection.test_old(DetectionData.from_json(json))

    return res.to_json_str_old()
