import time

import utils.utils as ut
import utils.regiondetection as regiondetection    

def search_image_all(self, img_path, sha_hash):
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

        poi = _region_find(self, img_path, sha_hash)
        
        regionFindSPT = time.time()
        self._main_logger.warn(f"Time elapsed for regionFind for {sha_hash} is {regionFindSPT - regionFindST}")
        
    try:
        reverseSearchST = time.time()
  
        for search_engine in self.search_engines:
            _rev_image_search(self, poi, search_engine, sha_hash)

        reverseSearchSPT = time.time()
        self._main_logger.warn(f"Time elapsed for reverseImgSearch for {sha_hash} is {reverseSearchSPT - reverseSearchST}")

        _text_search(self, search_engine, search_terms, sha_hash)

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

    poi, imgdata = regiondetection.findregions(img_path)
    self._main_logger.info("Regions found: " + str(len(poi)))
    
    try:
        self.conn_storage.execute("INSERT INTO screen_info (filepath, width, height, colourcount, dominant_colour_pct) VALUES (?, ?, ?, ?, ?)", 
                                  (sha_hash, imgdata[2], imgdata[1], imgdata[0][0], imgdata[0][1]))
        self._main_logger.debug("(filepath, region, width, height, xcoord, ycoord, colourcount, dominant_colour_pct, parent, child, invert)")
        
        for region in poi:
            h, w, _ = region[0].shape
            self._main_logger.debug(f"({sha_hash}, {region[1]}, {w}, {h}, {region[2]}, {region[3]}, {region[4]}, {region[5]}, {region[6][2]}, {region[6][3]})")
            logo_prob = self.clf_logo.predict_proba([[w, h, region[2], region[3], region[4], region[5], region[8], region[9], region[10], region[11], region[12], region[13], region[14], region[15]]])[:, 1][0]
            self.conn_storage.execute("INSERT INTO region_info (filepath, region, width, height, xcoord, ycoord, colourcount, dominant_colour_pct, parent, child, invert, mean, std, skew, kurtosis, entropy, otsu, energy, occupied_bins, label, logo_prob) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ? ,?, ?, ?)", 
                                      (sha_hash, region[1], w, h, region[2], region[3], region[4], region[5], region[6][2], region[6][3], region[7], region[8], region[9], region[10], region[11], region[12], region[13], region[14], region[15], "", logo_prob))
        if self.clearbit:
            self.conn_storage.execute("INSERT INTO region_info (filepath, region, width, height, xcoord, ycoord, colourcount, dominant_colour_pct, parent, child, invert, mean, std, skew, kurtosis, entropy, otsu, energy, occupied_bins, label, logo_prob) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ? ,?, ?, ?)", 
                                      (sha_hash, 9999, 0, 0, 0, 0, 0, 0, -1, -1, -1, 0, 0, 0, 0, 0, 0, 0, 0, "clearbit", 1))
        self.conn_storage.commit()
        
        return poi
        
    except Exception as err:
        self._main_logger.error(err, exc_info=True)
        self.conn_storage.rollback()


def _rev_image_search(self, poi, search_engine, sha_hash):
    """
    Reverse image search and store 7 image matches results. Also clearbit functionality.
    """

    # Reverse image searching the regions using the search engine
    if self.mode == "both" or self.mode == "image":
        topx = self.conn_storage.execute(f"select filepath, region, invert from region_info where filepath = '{sha_hash}' and label <> 'clearbit' ORDER BY logo_prob DESC LIMIT 3").fetchall()
        
        for region in poi:
            if not ((sha_hash, region[1], region[7]) in topx):
                continue
            
            self._main_logger.info(f"Handling region {region[1]}")

            res = search_engine.get_n_image_matches(self.htmlsession, region[0], n=7)
            count_entry = 0
            
            for result in res:
                self.conn_storage.execute("INSERT INTO search_result_image (filepath, search_engine, region, entry, result) VALUES (?, ?, ?, ?, ?)", (sha_hash, search_engine.name, region[1], count_entry, result))
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