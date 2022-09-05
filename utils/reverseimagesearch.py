import os
import sqlite3
import time
import sys
import numpy as np

from utils.customlogger import CustomLogger
import utils.utils as ut
import utils.uploader as uploader
import utils.regiondetection as regiondetection

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

    def search_image_all(self, img_path, shahash):
        self._main_logger.debug("Preparing for search info from: " + shahash)
        self._main_logger.info(f"Search mode: {self.mode}")

        search_terms = None
        if self.mode == "both" or self.mode == "text":
            search_terms = ut.get_search_term(self.folder, shahash)
            self._main_logger.info(f"Search terms found: {search_terms}")

        poi = None
        if self.mode == "both" or self.mode == "image":
            # Get all points on interest in two passthroughs to get both black on white and white on black.
            
            ######
            regionFindST = time.time()
            ######

            poi, imgdata = regiondetection.findregions(img_path)
            self._main_logger.info("Regions found: " + str(len(poi)))
            try:
                self.conn_storage.execute("INSERT INTO screen_info (filepath, width, height, colourcount, dominant_colour_pct) VALUES (?, ?, ?, ?, ?)", (shahash, imgdata[2], imgdata[1], imgdata[0][0], imgdata[0][1]))
                self._main_logger.debug("(filepath, region, width, height, xcoord, ycoord, colourcount, dominant_colour_pct, parent, child, invert)")
                for region in poi:
                    h, w, c = region[0].shape
                    self._main_logger.debug(f"({shahash}, {region[1]}, {w}, {h}, {region[2]}, {region[3]}, {region[4]}, {region[5]}, {region[6][2]}, {region[6][3]})")
                    logo_prob = self.clf_logo.predict_proba([[w, h, region[2], region[3], region[4], region[5], region[8], region[9], region[10], region[11], region[12], region[13], region[14], region[15]]])[:, 1][0]
                    self.conn_storage.execute("INSERT INTO region_info (filepath, region, width, height, xcoord, ycoord, colourcount, dominant_colour_pct, parent, child, invert, mean, std, skew, kurtosis, entropy, otsu, energy, occupied_bins, label, logo_prob) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ? ,?, ?, ?)", (shahash, region[1], w, h, region[2], region[3], region[4], region[5], region[6][2], region[6][3], region[7], region[8], region[9], region[10], region[11], region[12], region[13], region[14], region[15], "", logo_prob))
                if self.clearbit:
                    self.conn_storage.execute("INSERT INTO region_info (filepath, region, width, height, xcoord, ycoord, colourcount, dominant_colour_pct, parent, child, invert, mean, std, skew, kurtosis, entropy, otsu, energy, occupied_bins, label, logo_prob) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ? ,?, ?, ?)", (shahash, 9999, 0, 0, 0, 0, 0, 0, -1, -1, -1, 0, 0, 0, 0, 0, 0, 0, 0, "clearbit", 1))
                self.conn_storage.commit()
            except Exception as err:
                self._main_logger.error(err, exc_info=True)
                self.conn_storage.rollback()

            ######
            regionFindSPT = time.time()
            self._main_logger.warn(f"Time elapsed for regionFind for {shahash} is {regionFindSPT - regionFindST}")
            ######


        try:
            ######
            reverseSearchST = time.time()
            ######

            for search_engine in self.search_engines:
                # Reverse image searching the regions using the search engine
                if self.mode == "both" or self.mode == "image":
                    topx = self.conn_storage.execute(f"select filepath, region, invert from region_info where filepath = '{shahash}' and label <> 'clearbit' ORDER BY logo_prob DESC LIMIT 3").fetchall()
                    for region in poi:
                        if not ((shahash, region[1], region[7]) in topx):
                            continue
                        self._main_logger.info(f"Handling region {region[1]}")

                        res = search_engine.get_n_image_matches(self.htmlsession, region[0], n=7)
                        count_entry = 0
                        for result in res:
                            self.conn_storage.execute("INSERT INTO search_result_image (filepath, search_engine, region, entry, result) VALUES (?, ?, ?, ?, ?)", (shahash, search_engine.name, region[1], count_entry, result))
                            count_entry += 1
                            self.conn_storage.commit()
                    if self.clearbit:
                        self._main_logger.info(f"Handling clearbit logo")
                        res = search_engine.get_n_image_matches_clearbit(self.htmlsession, self.tld, n=7)
                        count_entry = 0
                        for result in res:
                            self.conn_storage.execute("INSERT INTO search_result_image (filepath, search_engine, region, entry, result) VALUES (?, ?, ?, ?, ?)", (shahash, "clearbit", 9999, count_entry, result))
                            count_entry += 1
                            self.conn_storage.commit()
                
                ######
                reverseSearchSPT = time.time()
                self._main_logger.warn(f"Time elapsed for reverseImgSearch for {shahash} is {reverseSearchSPT - reverseSearchST}")
                ######



                # Searching based on text
                if (self.mode == "both" or self.mode == "text") and search_terms:
                    self._main_logger.info(f"Started session: {self.htmlsession}")
                    res = search_engine.get_n_text_matches(self.htmlsession, search_terms, n=7)
                    count_entry = 0
                    for result in res:
                        self.conn_storage.execute("INSERT INTO search_result_text (filepath, search_engine, search_terms, entry, result) VALUES (?, ?, ?, ?, ?)", (shahash, search_engine.name, search_terms, count_entry, result))
                        count_entry += 1
                        self.conn_storage.commit()

                # Destroy all lingering chrome handles and setup proxies
                #self._main_logger.info("Killing lingering chrome proc")
                #os.system("killall -9 chrome")
        except Exception as err:
            self._main_logger.error(err, exc_info=True)
            self.conn_storage.rollback()
            return False
        #self.conn_storage.commit()
        return True

    def handle_folder(self, subfolder, shahash):
        self._main_logger.info("Opening folder: " + subfolder)

        if not os.path.isfile(os.path.join(subfolder, 'screen.png')):
            self._main_logger.error("No screen.png for: " + subfolder)
        else:
            if not self.search_image_all(os.path.join(subfolder, 'screen.png'), shahash):
                self.err += 1

    def files_scan(self, start=0, end=0):
        if not self.folder:
            raise ValueError('No folder is defined')

        self._main_logger.info("Starting in folder scan mode")
        self._main_logger.info("all dirs: " + str(self.folder))
        list_subfolders = [f.path for f in os.scandir(self.folder) if f.is_dir()]

        self.total = min(len(list_subfolders), end-start)
        self.start = time.time()

        self._main_logger.info("Retrieving already handled urls")
        handled = []
        handled_resp = self.conn_storage.execute("select distinct filepath from region_info").fetchall()
        for fp in handled_resp:
            handled.append(fp[0])
        self._main_logger.info(f"Obtained {len(handled)} already handled urls")
        self.count = len(handled)

        skip_cnt = 0
        for subfolder in list_subfolders:
            if subfolder in handled:
                self._main_logger.info(f"Url was previously handled, skipping to next")
                continue
            if skip_cnt < start:
                skip_cnt += 1
                continue
            if not os.path.isfile(os.path.join(subfolder, 'screen.png')) or  not os.path.isfile(os.path.join(subfolder, 'page.html')) :
                self._main_logger.info(f"Missing file entry for: {subfolder}")
                continue
            self.handle_folder(subfolder, os.path.basename(subfolder))
            self.count += 1
            if self.count == self.total:
                break
            ut.setstatus(f"{self.count}/{self.total} ({self.count/self.total*100}%) - {ut.timeString(self.start, self.count, self.total)}")

    def database_scan_constant(self, database, start = 0, end = 1000):
        self._main_logger.info("Using database to receive urls")
        self._main_logger.info("Retrieving urls from: " + str(database))

        conn_url      = sqlite3.connect(database, uri=True)
        self._main_logger.info("Connected to database with urls")

        self.start = time.time()
        self.total = min(int(conn_url.execute("select count(*) from urls").fetchall()[0][0])-int(start), int(end)-int(start))
        searched_dns_list = conn_url.execute(f"select sha1 from urls limit {start}, {end-start}").fetchall()

        self._main_logger.info("Obtained " + str(self.total) + " urls")

        self._main_logger.info("Retrieving already handled urls")
        handled = []
        handled_resp = self.conn_storage.execute("select distinct filepath from region_info").fetchall()
        for fp in handled_resp:
            handled.append(fp[0])
        self._main_logger.info(f"Obtained {len(handled)} already handled urls")
        self.count = len(handled)
        ut.setstatus(f"{self.count}/{self.total} ({round(1/self.total*100, 2)}%) - {ut.timeString(self.start, 1, self.total)}")

        for row in searched_dns_list:
            if row[0] in handled:
                self._main_logger.info(f"Url was previously handled, skipping to next")
                continue
            self.handle_folder(os.path.join(self.folder, row[0]), row[0])
            self.count += 1
            ut.setstatus(f"{self.count}/{self.total} ({round(self.count/self.total*100, 2)}%) - {ut.timeString(self.start, self.count, self.total)}")

    def database_scan(self, database, limit=0):
        self._main_logger.info("Using database to receive urls")
        self._main_logger.info("Retrieving urls from: " + str(database))

        conn_url      = sqlite3.connect(database, uri=True)
        self._main_logger.info("Connected to database with urls")

        limitstr = ""
        if limit > 0:
            limitstr = f" LIMIT 0,{limit}"

        self.start = time.time()
        self.total = int(conn_url.execute("select count(*) from (select max(html_sha256) from urls where (blacklist is null or blacklist = '') and (brand != '') and (error_code = '0' or error_code is null) group by html_sha256)").fetchall()[0][0]);
        searched_dns_list = conn_url.execute(f"select max(sha1) from urls where (blacklist is null or blacklist = '') and (brand != '') and (error_code = '0' or error_code is null) group by html_sha256 order by random() {limitstr}").fetchall()

        self._main_logger.info("Obtained " + str(self.total) + " urls")

        self._main_logger.info("Retrieving already handled urls")
        handled = []
        handled_resp = self.conn_storage.execute("select distinct filepath from region_info").fetchall()
        for fp in handled_resp:
            handled.append(fp[0])
        self._main_logger.info(f"Obtained {len(handled)} already handled urls")

        for row in searched_dns_list:
            if row[0] in handled:
                self._main_logger.info(f"Url was previously handled, skipping to next")
                continue
            self.handle_folder(os.path.join(self.folder, row[0]), row[0])
            self.count += 1
            ut.setstatus(f"{self.count}/{self.total} ({round(self.count/self.total*100, 2)}%) - {ut.timeString(self.start, self.count, self.total)}")

    def setup_storage(self):
        try:
            sql_q_db = '''
                CREATE TABLE IF NOT EXISTS "search_result_image" (
                            "filepath"	string,
                            "search_engine"	string,
                            "region"	integer,
                            "entry"	integer,
                            "result" string
                        );'''
            self.conn_storage.execute(sql_q_db)
            sql_q_db = '''
                CREATE TABLE IF NOT EXISTS "search_result_text" (
                            "filepath"	string,
                            "search_engine"	string,
                            "search_terms"	string,
                            "entry"	integer,
                            "result" string
                        );'''
            self.conn_storage.execute(sql_q_db)
            sql_q_db = '''
                CREATE TABLE IF NOT EXISTS "region_info" (
                            "filepath"	string,
                            "region"	integer,
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
