import base64
import os
import time

from PIL import Image
from selenium import webdriver
from selenium.webdriver.chrome.options import Options


class Parsing:
    # "files/" + hash(URL)
    store = None
    clientscreen = None

    def __init__(self, save_screenshots, imagedata, target_url, store):
        self.store = store
        self.clientscreen = save_screenshots

        if not os.path.exists(store):
            os.makedirs(store)

        if save_screenshots:
            st = len("data:image/png;base64,")
            image = bytes(imagedata, "ascii")
            image = image[st:]

            self.create_png(store, image)
        else:
            # get screenshot ourselves with fixed size
            options = Options()
            options.add_argument("--headless")

            driver = webdriver.Chrome(options=options)
            driver.set_window_size(1280, 768)
            driver.get(target_url)
            time.sleep(2) # TODO: find better alternative to making sure page is fully loaded
            driver.save_screenshot(store + "/screen.png")
            driver.quit()

    def create_png(self, store_path, image):
        with open(store_path + "/screen.png", "wb") as f:
            f.write(base64.decodebytes(image))

    def get_size(self):
        if self.clientscreen:
            image = Image.open(self.store + "/screen.png")
            return image.size
        else:
            return (1280, 768)
