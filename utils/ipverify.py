import requests
import json
import sys

import utils.customlogger as cl

from utils.customlogger import CustomLogger
main_logger = CustomLogger().main_logger

class IPChecker():
    current_ip = None
    def __init__(self):
        self.current_ip = self.get_ip()
        main_logger.info(f"Starting with IP: {self.current_ip}, will shutdown on change")

    def get_ip(self) -> str:
        req = requests.get("http://ifconfig.me/all.json")
        json_data = json.loads(req.text)
        return json_data['ip_addr']

    def validate_ip(self):
        main_logger.info(f"Validating IP")
        if self.current_ip != self.get_ip():
            main_logger.error('IP Adress changed, shutting down')
            sys.exit(1)
