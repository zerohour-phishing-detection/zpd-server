from collections.abc import AsyncIterator

from requests_html import HTMLSession
from sklearn.linear_model import LogisticRegression

import utils.region_detection as region_detection
from search_engines.image.base import ReverseImageSearchEngine
from utils.logging import main_logger
from utils.region_detection import RegionData
from utils.timing import TimeIt


class LogoFinder:
    """
    Finds logos within an image, and their origins.
    """
    reverse_image_search_engines: list[ReverseImageSearchEngine] = None
    folder: str = None
    htmlsession: HTMLSession = None
    clf_logo: LogisticRegression = None

    _logger = main_logger.getChild('utils.reverse_image_search')

    def __init__(
        self,
        reverse_image_search_engines: list[ReverseImageSearchEngine] = None,
        folder: str = None,
        htmlsession: HTMLSession = None,
        clf: LogisticRegression = None
    ):
        self.reverse_image_search_engines = reverse_image_search_engines
        self.folder = folder
        self.htmlsession = htmlsession
        self.clf_logo = clf

    async def run(self, img_path: str) -> AsyncIterator[str]:
        """
        Attempts to find logos (and their origins) in the image specified by the given path.

        Yields
        ------
        str
            The URL where it found the logo back online.
        """

        self._logger.debug("Preparing for search info")

        # Finds the regions in the image
        with TimeIt('Region finding'):
            region_predictions = self.find_logo_probas(img_path)

        for revimg_search_engine in self.reverse_image_search_engines:
            # For each reverse image search engine, try to find the origin of each logo region
            with TimeIt(f'Logo reverse image search using {revimg_search_engine.name}'):
                try:
                    async for res in self.find_logo_origins(region_predictions, revimg_search_engine):
                        yield res

                except Exception:
                    self._logger.error(f'Error while finding logo origins using search engine {revimg_search_engine.name}', exc_info=True)

    def find_logo_probas(self, img_path: str) -> list[tuple[RegionData, float]]:
        """
        Finds regions in an image, and calculates the probability of being a logo per region.

        Returns
        -------
        list[tuple[RegionData, float]]
            The list of logo-probability combinations: each region with their probability of being a logo.
        """

        regions, _ = region_detection.find_regions(img_path)
        self._logger.info(f"Found {len(regions)} regions")

        try:
            self._logger.debug(
                "(filepath, region, width, height, xcoord, ycoord, colourcount, dominant_colour_pct, parent, child, invert)"
            )

            region_probas = []
            for region_data in regions:
                height, width, _ = region_data.region.shape
                self._logger.debug(
                    f"({region_data.index}, {width}, {height}, {region_data.x}, {region_data.y}, {region_data.unique_colors_count}, {region_data.pct}, {region_data.hierarchy[2]}, {region_data.hierarchy[3]})"
                )

                logo_prob = self.clf_logo.predict_proba([
                    [
                        width,
                        height,
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
            self._logger.error(f'Exception while finding regions for img_path {img_path}', exc_info=True)

    async def find_logo_origins(self, logo_probas: list[tuple[RegionData, float]], revimg_search_engine: ReverseImageSearchEngine) -> AsyncIterator[str]:
        """
        Find the origin of the 3 highest-logo-probability regions, using the given search engine.
        """

        # Sort region predictions by logo probability, in descending order
        logo_probas.sort(key=lambda t: t[1], reverse=True)

        region_count = 0
        # TODO: concurrency here
        for region_data, logo_proba in logo_probas:
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
