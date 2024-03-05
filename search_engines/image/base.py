from typing import Iterator

import numpy as np

from utils.custom_logger import CustomLogger


class ReverseImageSearchEngine:
    """
    A class that allows you to make online reverse image search queries.
    """
    name: str

    main_logger = None

    def __init__(self, name):
        self.name = name
        self.main_logger = CustomLogger().main_logger

    def query(self, region: np.ndarray) -> Iterator[str]:
        """
        Performs a reverse image search query for the input region,
        returning an iterator of URL strings.
        """
        raise NotImplementedError()
