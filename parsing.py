import base64
import os

from PIL import Image
from selenium import webdriver
from selenium.webdriver.chrome.options import Options


class Parsing:
    # "files/" + hash(URL)
    store = None
    clientscreen = None

    def __init__(self, save_screenshots, title, imagedata, target_url, store):
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
            driver.save_screenshot(store + "/screen.png")
            driver.quit()

        self.create_html(store, title)

    def create_png(self, store_path, image):
        with open(store_path + "/screen.png", "wb") as f:
            f.write(base64.decodebytes(image))

    def create_html(self, store_path, title):
        with open(store_path + "/page.html", "w") as g:
            g.write("<title>" + title + "</title>")

    def get_size(self):
        if self.clientscreen:
            image = Image.open(self.store + "/screen.png")
            return image.size
        else:
            return (1280, 768)
