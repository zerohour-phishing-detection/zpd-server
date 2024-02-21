import os
import sqlite3
import numpy as np

from utils.customlogger import CustomLogger
from utils.searchimage import search_image_all

import searchengine

class ReverseImageSearch():
    search_engines = None
    folder = None
    conn_storage = None

    count = 0
    err = 0
    total = None
    start = None
    mode = None
    htmlsession = None
    clf_logo = None
    clearbit = False
    tld = None

    _main_logger = CustomLogger().main_logger

    def __init__(self, storage=None, search_engine=None, folder=None, upload=True, mode=None, htmlsession=None, clf=None, clearbit=False, tld=None):
        # To avoid ints becoming blobs upon storing:
        sqlite3.register_adapter(np.int64, lambda val: int(val))
        sqlite3.register_adapter(np.int32, lambda val: int(val))

        #self._main_logger.info(f"Starting with IP: {ut.get_ip()}")
        self.search_engines = searchengine.SearchEngine().get_engine(search_engine)
        #self._main_logger.info(f"Using the following search engine(s): {', '.join([en.name for en in self.search_engines])}")

        self.conn_storage = sqlite3.connect(storage)
        self.folder = folder
        self.upload = upload
        self.mode = mode
        self.htmlsession = htmlsession
        self.clf_logo = clf
        self.clearbit = clearbit
        self.tld = tld
        self.setup_storage()

    def handle_folder(self, subfolder, shahash):
        self._main_logger.info("Opening folder: " + subfolder)

        if not os.path.isfile(os.path.join(subfolder, 'screen.png')):
            self._main_logger.error("No screen.png for: " + subfolder)
        else:
            if not search_image_all(self, os.path.join(subfolder, 'screen.png'), shahash):
                self.err += 1

    def setup_storage(self):
        try:
            sql_q_db = '''
                CREATE TABLE IF NOT EXISTS "search_result_image" (
                            "filepath" string,
                            "search_engine" string,
                            "region" integer,
                            "entry"	integer,
                            "result" string
                        );'''
            self.conn_storage.execute(sql_q_db)
            
            sql_q_db = '''
                CREATE TABLE IF NOT EXISTS "search_result_text" (
                            "filepath" string,
                            "search_engine" string,
                            "search_terms" string,
                            "entry" integer,
                            "result" string
                        );'''
            self.conn_storage.execute(sql_q_db)
            
            sql_q_db = '''
                CREATE TABLE IF NOT EXISTS "region_info" (
                            "filepath" string,
                            "region" integer,
                            "width"	integer,
                            "height" integer,
                            "xcoord" integer,
                            "ycoord" integer,
                            "colourcount" integer,
                            "dominant_colour_pct" integer,
                            "child"	integer,
                            "parent" integer,
                            "invert" string,
                            "mean" float,
                            "std" float,
                            "skew" float,
                            "kurtosis" float,
                            "entropy" float,
                            "otsu" float,
                            "energy" float,
                            "occupied_bins" integer,
                            "label" string,
                            "logo_prob" float
                        );'''
            self.conn_storage.execute(sql_q_db)
            
            sql_q_db = '''
                CREATE TABLE IF NOT EXISTS "screen_info" (
                            "filepath"	string,
                            "width"	integer,
                            "height" integer,
                            "colourcount" integer,
                            "dominant_colour_pct" integer
                        );'''
            self.conn_storage.execute(sql_q_db)
            
            self.conn_storage.commit()
            
        except sqlite3.Error as er:
            self._main_logger.error("Failed to create table")
            self._main_logger.error(er)
