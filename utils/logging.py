import logging
import os
import time

main_logger: logging.Logger = logging.getLogger('zpd')
"""
The main logger to be used by the program.
"""

if not os.path.exists("logs"):
    os.makedirs("logs")

# Allow all log levels
main_logger.setLevel(logging.DEBUG)

def setup():
    global main_logger

    formatter_c = logging.Formatter(
        "%(asctime)s  [\033[93m%(pathname)s:%(lineno)d\033[0m]  %(levelname)s: %(message)s"
    )
    formatter_f = logging.Formatter(
        "%(asctime)s  [%(pathname)s:%(lineno)d]  %(levelname)s: %(message)s"
    )

    # Add console log handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formatter_c)
    main_logger.addHandler(console_handler)

    now = time.time()

    # Add main file log handler
    file_handler = logging.FileHandler(f"logs/python-{now}.log", mode="w")
    file_handler.setLevel(logging.INFO)
    file_handler.setFormatter(formatter_f)
    main_logger.addHandler(file_handler)

    # Add extra file log handler at ERROR level
    file_handler_error = logging.FileHandler(f"logs/error-{now}.log", mode="w")
    file_handler_error.setLevel(logging.ERROR)
    file_handler_error.setFormatter(formatter_f)
    main_logger.addHandler(file_handler_error)

    # Add extra file log handler at DEBUG level
    file_handler_debug = logging.FileHandler(f"logs/debug-{now}.log", mode="w")
    file_handler_debug.setLevel(logging.DEBUG)
    file_handler_debug.setFormatter(formatter_f)
    main_logger.addHandler(file_handler_debug)

setup()