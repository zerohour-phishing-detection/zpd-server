import os
import signal

# To avoid RuntimeError('This event loop is already running') when there are many of requests
import nest_asyncio
from flask import Flask, jsonify, render_template, request

import detection
from detection import DetectionData, DetectionSettings
from utils.logging import main_logger
from utils.registry import DECISION_STRATEGIES, DETECTION_METHODS

# __import__('IPython').embed()
nest_asyncio.apply()

# The storage interface for the sessions
session_storage = detection.session_storage

# Instantiate a logger for this HTTP API
logger = main_logger.getChild('api')

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


@app.route("/api/v1/capabilities", methods=["GET"])
def get_available_capabilities():
    result = [
        {
            "decision-strategy": list(DECISION_STRATEGIES.keys()),
            "detection-methods": list(DETECTION_METHODS.keys()),
        }
    ]
    print(list(DECISION_STRATEGIES.items())[0])
    return jsonify(result)


# Handle CTRL+C for shutdown
def signal_handler(sig, frame):
    shutdown_server()


signal.signal(signal.SIGINT, signal_handler)

if __name__ == "__main__":
    # Start Flask app, bind to all interfaces
    app.run(host="0.0.0.0")
