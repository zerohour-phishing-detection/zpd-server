import json
import base64
import os
from PIL import Image
from webdriver_manager.chrome import ChromeDriver
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.options import Options
from selenium import webdriver
import utils.regiondetection as rd

class Parsing():


    # "files/" + sha1hash(URL)
    store = None
    json = None
    clientscreen = None

    def __init__(self, clientscreen, json, store):
        self.json = json
        self.store = store
        self.clientscreen = clientscreen

        title = json['pagetitle']
        if not os.path.exists(store):
            os.makedirs(store)

        if clientscreen:
            st = len("data:image/png;base64,")
            image = bytes(json['image64'], 'ascii')
            image = image[st:]

            self.create_png(store, image)
        else:
            #get screenshot ourselves with fixed size
            target_URL = json['URL']
            options = Options()
            options.add_argument( "--headless" )

            #driver = webdriver.Chrome(ChromeDriverManager().install(), options=options)
            # replaces the above with a fixed ChromeDriver
            driver = webdriver.Chrome(options=options)
            driver.set_window_size(1280, 768)
            driver.get(target_URL)
            screenshot = driver.save_screenshot(store + "/screen.png")
            driver.quit()

        #rd.findregions(store + "/screen.png", draw=True, recursivedraw=True, highlightname="high-1")
        self.create_html(store, title)




        
    def create_png(self, store_path, image):
        with open(store_path + "/screen.png", "wb") as f:
            f.write(base64.decodebytes(image))
        #screen = Image.open(store_path + "/screen_uncropped.png")
        #width, height = screen.size
        #if width > 1280:
        #    r = 1280
        #if height > 768:
        #    b = 768
        #screen1 = screen.crop((0, 0, r, b))
        #screen1.save(store_path + "screen.png", format="png")
        
    def create_html(self, store_path, title):
        with open(store_path + "/page.html", "w") as g:
            g.write("<title>"+ title + "</title>")

    def get_size(self):
        if self.clientscreen:
            image = Image.open(self.store + "/screen.png")
            return image.size
        else:
            return (1280, 768)
