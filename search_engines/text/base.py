from typing import Iterator

from utils.custom_logger import main_logger


class TextSearchEngine:
    """
    A class that allows you to make online text search queries.
    """
    name: str

    logger = None

    def __init__(self, name):
        self.name = name
        self.logger = main_logger.getChild('text_search_engine.' + name)

    def query(self, text: str) -> Iterator[str]:
        """
        Performs a text search query for the input string `text`,
        returning an iterator of URL strings.
        """
        raise NotImplementedError()
