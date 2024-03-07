import logging
from typing import Iterator

import numpy as np

from utils.custom_logger import main_logger


class ReverseImageSearchEngine:
    """
    A class that allows you to make online reverse image search queries.
    """
    name: str
    logger: logging.Logger

    def __init__(self, name):
        self.name = name
        self.logger = main_logger.getChild('reverse_image_search_engine.' + name)

    def query(self, region: np.ndarray) -> Iterator[str]:
        """
        Performs a reverse image search query for the input region,
        returning an iterator of URL strings.
        """
        raise NotImplementedError()
