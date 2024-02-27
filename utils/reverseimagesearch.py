import os
import sqlite3
import time
import numpy as np

from utils.customlogger import CustomLogger
import utils.utils as ut
import utils.region_detection as region_detection
from utils.region_detection import RegionData

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

    def __init__(self, storage=None, search_engines=None, folder=None, upload=True, mode=None, htmlsession=None, clf=None, clearbit=False, tld=None):
        # To avoid ints becoming blobs upon storing:
        sqlite3.register_adapter(np.int64, lambda val: int(val))
        sqlite3.register_adapter(np.int32, lambda val: int(val))

        #self._main_logger.info(f"Starting with IP: {ut.get_ip()}")
        self.search_engines = search_engines
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
            if not self._search_image_all(os.path.join(subfolder, 'screen.png'), shahash):
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

    def _search_image_all(self, img_path, sha_hash):
        #TODO: Add docstring
        
        self._main_logger.debug("Preparing for search info from: " + sha_hash)
        self._main_logger.info(f"Search mode: {self.mode}")

        search_terms = None
        if self.mode == "both" or self.mode == "text":
            search_terms = ut.get_search_term(self.folder, sha_hash)
            self._main_logger.info(f"Search terms found: {search_terms}")

        poi = None
        if self.mode == "both" or self.mode == "image":
            # Get all points on interest in two passthroughs to get both black on white and white on black.

            regionFindST = time.time()

            poi = self._region_find(img_path, sha_hash)
            
            regionFindSPT = time.time()
            self._main_logger.warn(f"Time elapsed for regionFind for {sha_hash} is {regionFindSPT - regionFindST}")
            
        try:
            reverseSearchST = time.time()
    
            for search_engine in self.search_engines:
                self._rev_image_search(poi, search_engine, sha_hash)

            reverseSearchSPT = time.time()
            self._main_logger.warn(f"Time elapsed for reverseImgSearch for {sha_hash} is {reverseSearchSPT - reverseSearchST}")

            self._text_search(search_engine, search_terms, sha_hash)

        except Exception as err:
            self._main_logger.error(err, exc_info=True)
            self.conn_storage.rollback()
            return False

        return True

    def _region_find(self, img_path, sha_hash):
        """
        Find regions in an image, put the regions with attributes in the storage of self. 
        Calculate the probabilities of a region being a logo and store it.
        """

        poi, imgdata = region_detection.find_regions(img_path)
        self._main_logger.info("Regions found: " + str(len(poi)))
        
        try:
            self.conn_storage.execute("INSERT INTO screen_info (filepath, width, height, colourcount, dominant_colour_pct) VALUES (?, ?, ?, ?, ?)", 
                                    (sha_hash, imgdata[2], imgdata[1], imgdata[0][0], imgdata[0][1]))
            self._main_logger.debug("(filepath, region, width, height, xcoord, ycoord, colourcount, dominant_colour_pct, parent, child, invert)")
            
            for region_data in poi:
                h, w, _ = region_data.region.shape
                self._main_logger.debug(f"({sha_hash}, {region_data.index}, {w}, {h}, {region_data.x}, {region_data.y}, {region_data.unique_colors_count}, {region_data.pct}, {region_data.hierarchy[2]}, {region_data.hierarchy[3]})")
                logo_prob = self.clf_logo.predict_proba([[w, h, region_data.x, region_data.y, region_data.unique_colors_count, region_data.pct, region_data.mean, region_data.std, region_data.skew, region_data.kurtosis, region_data.entropy, region_data.otsu, region_data.energy, region_data.occupied_bins]])[:, 1][0]
                self.conn_storage.execute("INSERT INTO region_info (filepath, region, width, height, xcoord, ycoord, colourcount, dominant_colour_pct, parent, child, invert, mean, std, skew, kurtosis, entropy, otsu, energy, occupied_bins, label, logo_prob) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ? ,?, ?, ?)", 
                                        (sha_hash, region_data.index, w, h, region_data.x, region_data.y, region_data.unique_colors_count, region_data.pct, region_data.hierarchy[2], region_data.hierarchy[3], region_data.invert, region_data.mean, region_data.std, region_data.skew, region_data.kurtosis, region_data.entropy, region_data.otsu, region_data.energy, region_data.occupied_bins, "", logo_prob))
            if self.clearbit:
                self.conn_storage.execute("INSERT INTO region_info (filepath, region, width, height, xcoord, ycoord, colourcount, dominant_colour_pct, parent, child, invert, mean, std, skew, kurtosis, entropy, otsu, energy, occupied_bins, label, logo_prob) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ? ,?, ?, ?)", 
                                        (sha_hash, 9999, 0, 0, 0, 0, 0, 0, -1, -1, -1, 0, 0, 0, 0, 0, 0, 0, 0, "clearbit", 1))
            self.conn_storage.commit()
            
            return poi
            
        except Exception as err:
            self._main_logger.error(err, exc_info=True)
            self.conn_storage.rollback()

    def _rev_image_search(self, poi : list[RegionData], search_engine, sha_hash):
        """
        Reverse image search and store 7 image matches results. Also clearbit functionality.
        """

        # Reverse image searching the regions using the search engine
        if self.mode == "both" or self.mode == "image":
            topx = self.conn_storage.execute(f"select filepath, region, invert from region_info where filepath = '{sha_hash}' and label <> 'clearbit' ORDER BY logo_prob DESC LIMIT 3").fetchall()
            
            for region_data in poi:
                if not ((sha_hash, region_data.index, region_data.invert) in topx):
                    continue
                
                self._main_logger.info(f"Handling region {region_data.index}")

                res = search_engine.get_n_image_matches(self.htmlsession, region_data.region, n=7)
                count_entry = 0
                
                for result in res:
                    self.conn_storage.execute("INSERT INTO search_result_image (filepath, search_engine, region, entry, result) VALUES (?, ?, ?, ?, ?)", (sha_hash, search_engine.name, region_data[1], count_entry, result))
                    count_entry += 1
                    self.conn_storage.commit()
                    
            if self.clearbit:
                self._main_logger.info(f"Handling clearbit logo")
                res = search_engine.get_n_image_matches_clearbit(self.htmlsession, self.tld, n=7)
                count_entry = 0
                
                for result in res:
                    self.conn_storage.execute("INSERT INTO search_result_image (filepath, search_engine, region, entry, result) VALUES (?, ?, ?, ?, ?)", (sha_hash, "clearbit", 9999, count_entry, result))
                    count_entry += 1
                    self.conn_storage.commit()

    def _text_search(self, search_engine, search_terms, sha_hash):
        """
        Look up and store 7 results of search_terms using the search engine.
        """
        
        # Searching based on text
        if (self.mode == "both" or self.mode == "text") and search_terms:
            self._main_logger.info(f"Started session: {self.htmlsession}")
            res = search_engine.get_n_text_matches(self.htmlsession, search_terms, n=7)
            count_entry = 0
            
            for result in res:
                self.conn_storage.execute("INSERT INTO search_result_text (filepath, search_engine, search_terms, entry, result) VALUES (?, ?, ?, ?, ?)", (sha_hash, search_engine.name, search_terms, count_entry, result))
                count_entry += 1
                self.conn_storage.commit()