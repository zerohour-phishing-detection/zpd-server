import os
import signal

# To avoid RuntimeError('This event loop is already running') when there are many of requests
import nest_asyncio
from flask import Flask, jsonify, render_template, request

import detection
from api_versions.v1 import v1
from api_versions.v2 import v2
from utils.logging import main_logger
from utils.registry import DECISION_STRATEGIES, DETECTION_METHODS

nest_asyncio.apply()

# The storage interface for the sessions
session_storage = detection.session_storage

# Instantiate a logger for this HTTP API
logger = main_logger.getChild("api")

# Initiate Flask app
app = Flask(__name__)
app.config["DEBUG"] = False


@app.route("/")
def home():
    return render_template("index.html")


def shutdown_server():
    os._exit(0)



@v1.route("/url/state", methods=["POST"])
@v2.route("/url/state", methods=["POST"])
def get_url_state():
    json = request.get_json()
    url = json["URL"]
    uuid = json["uuid"]

    session = session_storage.get_session(uuid, url)
    status = session.get_state()

    result = [{"status": status.result, "state": status.state}]

    return jsonify(result)


@v1.route("/capabilities", methods=["GET"])
@v2.route("/capabilities", methods=["GET"])
def get_available_capabilities():
    result = [
        {
            "decision-strategy": list(DECISION_STRATEGIES.keys()),
            "detection-methods": list(DETECTION_METHODS.keys()),
        }
    ]
    print(list(DECISION_STRATEGIES.items())[0])
    return jsonify(result)


app.register_blueprint(v1, url_prefix="/api/v1")
app.register_blueprint(v2, url_prefix="/api/v2")


# Handle CTRL+C for shutdown
def signal_handler(sig, frame):
    shutdown_server()


signal.signal(signal.SIGINT, signal_handler)

if __name__ == "__main__":
    # Start Flask app, bind to all interfaces
    app.run(host="0.0.0.0")
