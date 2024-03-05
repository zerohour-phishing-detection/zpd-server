from typing import Iterator

from utils.custom_logger import CustomLogger


class TextSearchEngine:
    """
    A class that allows you to make online text search queries.
    """
    name: str

    main_logger = None

    def __init__(self, name):
        self.name = name
        self.main_logger = CustomLogger().main_logger

    def query(self, text: str) -> Iterator['str']:
        """
        Performs a text search query for the input string `text`,
        returning an iterator of URL strings.
        """
        raise NotImplementedError()
