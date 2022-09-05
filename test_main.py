# General Libraries
import argparse
import os
import time

# Util libs
from utils.reverseimagesearch import ReverseImageSearch
from engines.google import GoogleReverseImageSearchEngine

import searchengine
# Setup logging
from utils.customlogger import CustomLogger
main_logger = CustomLogger().main_logger


# def_base = "/media/root/Samsung_T5/phishing-db/benign"
def_base = "/media/root/Samsung_T5/phishing-db/benign"
if not os.path.exists(def_base):
    def_base_vm = "/media/sf_Samsung_T5/phishing-db/benign"
    if os.path.exists(def_base_vm):
        main_logger.info("VM folders detected. setting default variables to VM.")
        def_base = def_base_vm
    else:
        def_base = ""

def_db = "db/test_urls.db"
def_storage = "db/test_output.db"
def_folder = "files/"

# MISSING: star browser session?
htmlsession = HTMLSession()
htmlsession.browser

# Setup arg parser
parser = argparse.ArgumentParser()
parser.add_argument('--storage', default=def_storage, help='Where to store the results')
parser.add_argument('--engine', help='What search engine to use', choices=searchengine.SearchEngine().get_identifiers(), default=list(GoogleReverseImageSearchEngine().identifiers())[0])
parser.add_argument('--folder', default=def_folder, help='Where the local data is')
parser.add_argument('--db', default=def_db, help='database containing urls')
parser.add_argument('--start', default=0, type=int, help='What entry to start on')
parser.add_argument('--end', default=1000, type=int, help='What entry to end on')
parser.add_argument('--mode', choices=["image", "text", "both"], default="both", help='What mode to perform search in')
args = parser.parse_args()

main_logger.info("Finished boot sequence.")

search = ReverseImageSearch(storage=args.storage, search_engine=args.engine, folder=args.folder, upload=True, mode=args.mode)

search.database_scan_constant(database=args.db, start=args.start, end=args.end)

# import utils.regiondetection as rd
# rd.findregions("Capture.png", draw=True, recursivedraw=True, highlightname="high-1")

# Double checking missing entries
# import utils.utils as ut
# ut.fix_entries(search, def_db)
main_logger.info("Finished Program")
