from flask import Flask, request, jsonify, render_template

from utils.customlogger import CustomLogger
import os
import signal

import detection

# To avoid RuntimeError('This event loop is already running') when there are many of requests
import nest_asyncio
#__import__('IPython').embed()
nest_asyncio.apply()


# The storage interface for the sessions
session_storage = detection.session_storage

# The main logger for the whole program, singleton
main_logger = CustomLogger().main_logger

# Initiate Flask app
app = Flask(__name__)
app.config["DEBUG"] = False


@app.route('/')
def home():
    return render_template('index.html')

@app.route('/stop')
def shutdown():
    shutdown_server()
    return 'Server shutting down...'

def shutdown_server():
    os._exit(0)

@app.route('/api/v1/url', methods=['POST'])
def check_url():
    json = request.get_json()
    
    # main_logger.debug("Received JSON: " + str(json))
    # main_logger.warn("Received JSON: " + str(json))
    # main_logger.warn("Received JSON: " + str(json["URL"]))
        
    url = json["URL"]
    screenshot_url = url # the actual URL to screenshot
    
    # extra json field for evaluation purposes
    # the hash computed in the DB is the this one
    if "phishURL" in json: # TODO only allow this on a testing environment, not prod
        url = json["phishURL"]
        main_logger.info(f"Real URL changed to phishURL: {url}\n")
    
    uuid = json["uuid"]
    pagetitle = json['pagetitle']
    image64 = json['image64']
    
    res = detection.test(url, screenshot_url, uuid, pagetitle, image64)

    return res.to_json_str()
    
@app.route('/api/v1/url/state', methods=['POST'])
def get_url_state():
    json = request.get_json()
    url = json["URL"]
    uuid = json["uuid"]
    
    session = session_storage.get_session(uuid, url)
    status = session.get_state()
    
    result = [{'status': status.result, 'state': status.state}]
    return jsonify(result)


# Handle CTRL+C for shutdown
def signal_handler(sig, frame):
    shutdown_server()
signal.signal(signal.SIGINT, signal_handler)

# Start Flask app, bind to all interfaces
app.run(host="0.0.0.0")
