import requests
from bs4 import BeautifulSoup
import cv2
from numpy import ndarray
import os
from ratelimit import limits, sleep_and_retry
import random

# Setup logging
from utils.customlogger import CustomLogger
main_logger = CustomLogger().main_logger

@sleep_and_retry
@limits(calls=1, period=10)
def upload(image, avoid=None):
    raise NotImplementedError