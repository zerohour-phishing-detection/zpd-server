import os
import time

from selenium import webdriver
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.chrome.options import Options


class ScreenShotter:
    """
    A utility class that helps with taking screenshots of webpages from URLs.
    """
    driver: webdriver.Chrome

    def __init__(self, window_size: tuple[int, int] = (1280, 768)):
        """
        Instantiates a new screenshotter.

        Parameters
        ----------
        window_size: tuple[int, int]
            The image size of the resulting screenshots as a `(width, height)` tuple.
        """
        options = Options()
        # Prevent automatic download of .pdf files
        prefs = {
            "download.default_directory": "/dev/null"
        }
        options.add_experimental_option(
            "prefs", prefs
        )

        options.add_argument("--headless")

        self.driver = webdriver.Chrome(options=options)
        self.driver.set_window_size(*window_size)
        self.driver.set_page_load_timeout(5)
    
    def _visit(self, url: str):
        """
        Visits the given URL, and wait for it to be loaded.
        """
        # First, go to the new tab page so .pdf files (that dont change the window) dont show the last opened website instead
        # TODO: improve solution to these pdf shenanigans, if possible
        self.driver.get('chrome://newtab')
        print('newtab visited')

        try:
            self.driver.get(url)
        except TimeoutException as e:
            raise Exception(e.msg)
            
        
        print('actual url visited')
        
        time.sleep(2) # TODO: find better alternative to making sure page is fully loaded
        
        print('slept')

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
        print('url visited')

        # Create directory if needed
        if mkdirs:
            parent = os.path.dirname(filepath)
            if len(parent) != 0 and not os.path.exists(parent):
                os.makedirs(parent)

        self.driver.save_screenshot(filepath)
    
    def get_window_size(self) -> tuple[int, int]:
        """
        Gets the window size of screenshots.
         
        Returns
        -------
        (width, height): tuple[int, int]
        """
        return tuple(self.driver.get_window_size().values())

    def close(self):
        """
        Closes this screenshotter. After closing, do not keep using this instance.
        """
        self.driver.close()

screenshotter = ScreenShotter()
