import asyncio
import os
from collections.abc import AsyncIterator

from requests_html import HTMLSession
from sklearn.linear_model import LogisticRegression

import utils.region_detection as region_detection
from search_engines.image.base import ReverseImageSearchEngine
from utils.logging import main_logger
from utils.region_detection import RegionData
from utils.timing import TimeIt


class ReverseImageSearch:
    reverse_image_search_engines: list[ReverseImageSearchEngine] = None
    folder = None

    count = 0
    err = 0
    total = None
    start = None
    htmlsession = None
    clf_logo: LogisticRegression = None

    _logger = main_logger.getChild('utils.reverse_image_search')

    def __init__(
        self,
        reverse_image_search_engines: list[ReverseImageSearchEngine] = None,
        folder: str = None,
        upload: bool = True,
        htmlsession: HTMLSession = None,
        clf: LogisticRegression = None
    ):
        self.reverse_image_search_engines = reverse_image_search_engines
        self.folder = folder
        self.upload = upload
        self.htmlsession = htmlsession
        self.clf_logo = clf

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

    async def _search_image_all(self, img_path: str, sha_hash: str) -> AsyncIterator[str]:
        # TODO: Add docstring

        self._logger.debug("Preparing for search info from: " + sha_hash)
        
        # Get all points on interest in two passthroughs to get both black on white and white on black.

        with TimeIt('Region finding'):
            region_predictions = self._region_find(img_path, sha_hash)

        try:
            with TimeIt('reverse image search'):
                for revimg_search_engine in self.reverse_image_search_engines:
                    async for res in self._rev_image_search(region_predictions, revimg_search_engine, sha_hash):
                        yield res

        except Exception as err:
            self._logger.error(err, exc_info=True)

    def _region_find(self, img_path: str, sha_hash: str) -> list[tuple[RegionData, float]]:
        """
        Find regions in an image, put the regions with attributes in the storage of self.
        Calculate the probabilities of a region being a logo and store it.
        """

        poi, _ = region_detection.find_regions(img_path)
        self._logger.info(f"Found {len(poi)} regions")

        try:
            self._logger.debug(
                "(filepath, region, width, height, xcoord, ycoord, colourcount, dominant_colour_pct, parent, child, invert)"
            )

            region_probas = []
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

                region_probas.append((region_data, logo_prob))

            return region_probas

        except Exception:
            self._logger.error(f'Exception while finding regions for img_path {img_path} and hash {sha_hash}', exc_info=True)

    async def _rev_image_search(self, region_predictions: list[tuple[RegionData, float]], revimg_search_engine: ReverseImageSearchEngine, sha_hash: str) -> AsyncIterator[str]:
        """
        Reverse image search and store 7 image matches results.
        """

        # Sort region predictions by logo probability, in descending order
        region_predictions.sort(key=lambda t: t[1], reverse=True)

        region_count = 0
        # TODO: concurrency here
        for region_data, logo_proba in region_predictions:
            # if (sha_hash, region_data.index, region_data.invert) not in topx:
            #     continue

            self._logger.info(f"Handling region {region_data.index}, with logo proba {logo_proba}")

            count = 0
            for res in revimg_search_engine.query(region_data.region):
                yield res
                
                count += 1
                if count >= 7:
                    break

            region_count += 1
            if region_count >= 3:
                break
