import logging
import os
import time
import requests

class CustomLogger():
    """
    Singleton instance for logging, use `CustomLogger().main_logger` to get the instance.
    """
    _instance = None
    main_logger = None
    loggerid = None

    def __new__(self):
        if self._instance is None:
            self._instance = super().__new__(self)
            self._instance._setup()
        return self._instance

    def _setup(self):
        if not os.path.exists('log'):
            os.makedirs('log')
        self.loggerid = self.get_ip()

        self.main_logger = logging.getLogger("mainlogger")
        self.main_logger.setLevel(logging.DEBUG)

        formatter_c = logging.Formatter('%(asctime)s  [\033[93m%(pathname)s:%(lineno)d\033[0m]  %(levelname)s: %(message)s')
        formatter_f = logging.Formatter('%(asctime)s  [%(pathname)s:%(lineno)d]  %(levelname)s: %(message)s')

        consoleHandler = logging.StreamHandler()
        consoleHandler.setLevel(logging.INFO)
        consoleHandler.setFormatter(formatter_c)
        self.main_logger.addHandler(consoleHandler)

        fileHandler = logging.FileHandler(f"log/python-{time.time()}.log", mode='w')
        fileHandler.setLevel(logging.INFO)
        fileHandler.setFormatter(formatter_f)
        self.main_logger.addHandler(fileHandler)

        fileHandlerE = logging.FileHandler(f"log/error-{time.time()}.log", mode='w')
        fileHandlerE.setLevel(logging.ERROR)
        fileHandlerE.setFormatter(formatter_f)
        self.main_logger.addHandler(fileHandlerE)
        
        fileHandlerD = logging.FileHandler(f"log/debug-{time.time()}.log", mode='w')
        fileHandlerD.setLevel(logging.DEBUG)
        fileHandlerD.setFormatter(formatter_f)
        self.main_logger.addHandler(fileHandlerD)

        return self.main_logger

    def get_ip(self):
        response = requests.post("http://ident.me")
        return response.text
