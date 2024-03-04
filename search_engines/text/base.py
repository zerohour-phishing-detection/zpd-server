from typing import Iterator

from utils.custom_logger import CustomLogger


class TextSearchEngine:
    """
    A class that allows you to make online text search queries.
    """
    name: str = "Base"

    main_logger = None

    def __init__(self, name=None):
        self.name = name
        self.main_logger = CustomLogger().main_logger

    def query(self, text: str) -> Iterator['str']:
        """
        Performs a text search query for the input string `text`
        expecting `n` results.
        """
        raise NotImplementedError()
