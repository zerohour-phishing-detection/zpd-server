from utils.reverseimagesearch import ReverseImageSearch
from engines.google import GoogleReverseImageSearchEngine
from requests_html import HTMLSession
import os
import sqlite3
from distutils.dir_util import copy_tree
import shutil


htmlsession = HTMLSession()
htmlsession.browser

# mode = "phishing"
mode = "benign"

def_folder = f"{mode}-rawdata/{mode}/files"
def_storage = f"db/new_region_data_{mode}.db" 
# new_folder = f"{mode}-rawdata/{mode}/sample"
new_folder = f"{mode}-rawdata/{mode}/sample2"

conn_storage = sqlite3.connect(def_storage)

list_name = os.listdir(def_folder)

# for i in range(3000):
for i in range(7):
    if not os.path.exists(os.path.join(new_folder, list_name[i])):
        shutil.copytree(os.path.join(def_folder, list_name[i]), os.path.join(new_folder, list_name[i]))
    search = ReverseImageSearch(storage=def_storage, search_engine=list(GoogleReverseImageSearchEngine().identifiers())[0], folder=def_folder, upload=False, mode="image", htmlsession=htmlsession)
    search.handle_folder(os.path.join(new_folder, list_name[i]), list_name[i])
