import os
import signal

# To avoid RuntimeError('This event loop is already running') when there are many of requests
import nest_asyncio
from flask import Flask, jsonify, render_template, request

import detection
from detection import DetectionData, DetectionSettings
from methods.detection_methods import DetectionMethods
from utils.custom_logger import CustomLogger
from utils.decision import DecisionStrategies

# __import__('IPython').embed()
nest_asyncio.apply()

# The storage interface for the sessions
session_storage = detection.session_storage

# The main logger for the whole program, singleton
main_logger = CustomLogger().main_logger

# Initiate Flask app
app = Flask(__name__)
app.config["DEBUG"] = False


@app.route("/")
def home():
    return render_template("index.html")


def shutdown_server():
    os._exit(0)


# DEPRECATED
@app.route("/api/v1/url", methods=["POST"])
def check_url_old():
    json = request.get_json()

    res = detection.test_old(DetectionData.from_json(json))

    return res.to_json_str_old()


@app.route("/api/v2/url", methods=["POST"])
def check_url():
    json = request.get_json()
    json_data = json["data"]
    json_settings = json["settings"]

    res = detection.test(
        DetectionData.from_json(json_data), DetectionSettings.from_json(json_settings)
    )

    return res.to_json_str()


@app.route("/api/v1/url/state", methods=["POST"])
def get_url_state():
    json = request.get_json()
    url = json["URL"]
    uuid = json["uuid"]

    session = session_storage.get_session(uuid, url)
    status = session.get_state()

    result = [{"status": status.result, "state": status.state}]

    return jsonify(result)


@app.route("/api/v1/methods", methods=["GET"])
def get_available_methods():
    result = [
        {
            "decision-strategy": DecisionStrategies._member_names_,
            "detection-methods": DetectionMethods._member_names_,
        }
    ]
    return jsonify(result)


# Handle CTRL+C for shutdown
def signal_handler(sig, frame):
    shutdown_server()


signal.signal(signal.SIGINT, signal_handler)

# Start Flask app, bind to all interfaces
app.run(host="0.0.0.0")
