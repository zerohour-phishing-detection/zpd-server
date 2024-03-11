import asyncio
import os
import sqlite3
from collections.abc import AsyncIterator

import numpy as np
from requests_html import HTMLSession

import utils.region_detection as region_detection
from search_engines.image.base import ReverseImageSearchEngine
from utils.logging import main_logger
from utils.region_detection import RegionData
from utils.timing import TimeIt


class ReverseImageSearch:
    reverse_image_search_engines: list[ReverseImageSearchEngine] = None
    folder = None
    conn_storage = None

    count = 0
    err = 0
    total = None
    start = None
    htmlsession = None
    clf_logo = None

    _logger = main_logger.getChild('utils.reverse_image_search')

    def __init__(
        self,
        storage: str = None,
        reverse_image_search_engines: list[ReverseImageSearchEngine] = None,
        folder: str = None,
        upload: bool = True,
        htmlsession: HTMLSession = None,
        clf=None
    ):
        # To avoid ints becoming blobs upon storing:
        sqlite3.register_adapter(np.int64, lambda val: int(val))
        sqlite3.register_adapter(np.int32, lambda val: int(val))

        self.conn_storage = sqlite3.connect(storage)
        self.reverse_image_search_engines = reverse_image_search_engines
        self.folder = folder
        self.upload = upload
        self.htmlsession = htmlsession
        self.clf_logo = clf
        self.setup_storage()

    def handle_folder(self, subfolder: str, shahash: str) -> list[str] | None:
        self._logger.info("Opening folder: " + subfolder)

        if not os.path.isfile(os.path.join(subfolder, "screen.png")):
            self._logger.error("No screen.png for: " + subfolder)
        else:
            async def search_images():
                results = []
                async for x in self._search_image_all(os.path.join(subfolder, "screen.png"), shahash):
                    results.append(x)
                return results
            res = asyncio.run(search_images())
            
            if res is None:
                self.err += 1
            else:
                return res

    def setup_storage(self):
        try:
            sql_q_db = """
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
                        );"""
            self.conn_storage.execute(sql_q_db)

            sql_q_db = """
                CREATE TABLE IF NOT EXISTS "screen_info" (
                            "filepath"	string,
                            "width"	integer,
                            "height" integer,
                            "colourcount" integer,
                            "dominant_colour_pct" integer
                        );"""
            self.conn_storage.execute(sql_q_db)

            self.conn_storage.commit()

        except sqlite3.Error as er:
            self._logger.error("Failed to create table")
            self._logger.error(er)

    async def _search_image_all(self, img_path: str, sha_hash: str) -> AsyncIterator[str]:
        # TODO: Add docstring

        self._logger.debug("Preparing for search info from: " + sha_hash)
        
        # Get all points on interest in two passthroughs to get both black on white and white on black.

        with TimeIt('Region finding'):
            poi = self._region_find(img_path, sha_hash)

        try:
            with TimeIt('reverse image search'):
                for revimg_search_engine in self.reverse_image_search_engines:
                    async for res in self._rev_image_search(poi, revimg_search_engine, sha_hash):
                        yield res

        except Exception as err:
            self._logger.error(err, exc_info=True)
            self.conn_storage.rollback()

    def _region_find(self, img_path: str, sha_hash: str):
        """
        Find regions in an image, put the regions with attributes in the storage of self.
        Calculate the probabilities of a region being a logo and store it.
        """

        poi, imgdata = region_detection.find_regions(img_path)
        self._logger.info("Regions found: " + str(len(poi)))

        try:
            self.conn_storage.execute(
                "INSERT INTO screen_info (filepath, width, height, colourcount, dominant_colour_pct) VALUES (?, ?, ?, ?, ?)",
                (sha_hash, imgdata[2], imgdata[1], imgdata[0][0], imgdata[0][1]),
            )
            self._logger.debug(
                "(filepath, region, width, height, xcoord, ycoord, colourcount, dominant_colour_pct, parent, child, invert)"
            )

            for region_data in poi:
                h, w, _ = region_data.region.shape
                self._logger.debug(
                    f"({sha_hash}, {region_data.index}, {w}, {h}, {region_data.x}, {region_data.y}, {region_data.unique_colors_count}, {region_data.pct}, {region_data.hierarchy[2]}, {region_data.hierarchy[3]})"
                )
                logo_prob = self.clf_logo.predict_proba([
                    [
                        w,
                        h,
                        region_data.x,
                        region_data.y,
                        region_data.unique_colors_count,
                        region_data.pct,
                        region_data.mean,
                        region_data.std,
                        region_data.skew,
                        region_data.kurtosis,
                        region_data.entropy,
                        region_data.otsu,
                        region_data.energy,
                        region_data.occupied_bins,
                    ]
                ])[:, 1][0]
                self.conn_storage.execute(
                    "INSERT INTO region_info (filepath, region, width, height, xcoord, ycoord, colourcount, dominant_colour_pct, parent, child, invert, mean, std, skew, kurtosis, entropy, otsu, energy, occupied_bins, label, logo_prob) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ? ,?, ?, ?)",
                    (
                        sha_hash,
                        region_data.index,
                        w,
                        h,
                        region_data.x,
                        region_data.y,
                        region_data.unique_colors_count,
                        region_data.pct,
                        region_data.hierarchy[2],
                        region_data.hierarchy[3],
                        region_data.invert,
                        region_data.mean,
                        region_data.std,
                        region_data.skew,
                        region_data.kurtosis,
                        region_data.entropy,
                        region_data.otsu,
                        region_data.energy,
                        region_data.occupied_bins,
                        "",
                        logo_prob,
                    ),
                )
            self.conn_storage.commit()

            return poi

        except Exception as err:
            self._logger.error(err, exc_info=True)
            self.conn_storage.rollback()

    async def _rev_image_search(self, poi: list[RegionData], revimg_search_engine: ReverseImageSearchEngine, sha_hash: str) -> AsyncIterator[str]:
        """
        Reverse image search and store 7 image matches results.
        """

        # Reverse image searching the regions using the search engine
        topx = self.conn_storage.execute(
            f"select filepath, region, invert from region_info where filepath = '{sha_hash}' and label <> 'clearbit' ORDER BY logo_prob DESC LIMIT 3"
        ).fetchall()

        # TODO: concurrency here
        for region_data in poi:
            if (sha_hash, region_data.index, region_data.invert) not in topx:
                continue

            self._logger.info(f"Handling region {region_data.index}")

            count = 0
            for res in revimg_search_engine.query(region_data.region):
                yield res
                
                count += 1
                if count >= 7:
                    break
