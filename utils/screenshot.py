import os
import time

from selenium import webdriver
from selenium.webdriver.chrome.options import Options


class ScreenShotter:
    """
    A utility class that helps with taking screenshots of webpages from URLs.
    """
    driver: webdriver.Chrome

    def __init__(self):
        options = Options()
        options.add_argument("--headless")

        self.driver = webdriver.Chrome(options=options)
        self.driver.set_window_size(1280, 768)
    
    def _visit(self, url: str):
        """
        Visits the given URL, and wait for it to be loaded.
        """
        self.driver.get(url)
        time.sleep(2) # TODO: find better alternative to making sure page is fully loaded

    def get_screenshot(self, url: str) -> bytes:
        """
        Takes a screenshot of the given URL, returning it as PNG data bytes.

        Parameters
        ----------
        url: str
            The URL to take a screenshot of
        
        Returns
        -------
        bytes
            The PNG-encoded screenshot
        """
        self._visit(url)
        return self.driver.get_screenshot_as_png()
    
    def get_screenshot_base64(self, url: str) -> str:
        """
        Takes a screenshot of the given URL, returning it as base64 encoded PNG data.

        Parameters
        ----------
        url: str
            The URL to take a screenshot of
        
        Returns
        -------
        str
            The base64-encoded PNG image data
        """
        self._visit(url)
        return self.driver.get_screenshot_as_base64()

    def save_screenshot(self, url: str, filepath: str, mkdirs: bool = True):
        """
        Takes a screenshot of the given URL, and stores it as a PNG file.
        Also creates the parent directory for the screenshot if needed.

        Parameters
        ----------
        url: str
            The URL to take a screenshot of
        filename: str
            The filename to store the screenshot in, should end in `.png`
        mkdirs: bool = True
            Whether to create the parent directory for the screenshot file
            (True: create parent dirs, False: don't create parent dirs)
        """
        self._visit(url)

        # Create directory if needed
        if mkdirs:
            parent = os.path.dirname(filepath)
            if not os.path.exists(parent):
                os.makedirs(parent)

        self.driver.save_screenshot(filepath)
