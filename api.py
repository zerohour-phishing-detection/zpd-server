import os
import signal

import nest_asyncio

# To avoid RuntimeError('This event loop is already running') when there are many of requests
from flask import Flask, render_template

import detection
from api_versions.v1 import v1
from api_versions.v2 import v2
from utils.logging import main_logger

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


app.register_blueprint(v1, url_prefix="/api/v1")
app.register_blueprint(v2, url_prefix="/api/v2")


# Handle CTRL+C for shutdown
def signal_handler(sig, frame):
    shutdown_server()


signal.signal(signal.SIGINT, signal_handler)

if __name__ == "__main__":
    # Start Flask app, bind to all interfaces
    app.run(host="0.0.0.0")
