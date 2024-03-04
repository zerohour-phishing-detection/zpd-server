from urllib.parse import quote_plus

import requests
from ratelimit import limits, sleep_and_retry

from utils.custom_logger import CustomLogger
from utils.proxy_getter import ProxyGetter


class TextSearchEngine:
    """
    A class that allows you to make online search queries.
    """
    name = "Base"
    proxypool = ProxyGetter()

    main_logger = None

    search_html = None
    search_url = None

    def __init__(self, url_base, url_path, name=None):
        self.url_base = url_base
        self.url_path = url_path
        self.name = name
        self.main_logger = CustomLogger().main_logger

    def get_search_link_by_terms(self, search_term: str) -> str:
        self.search_html = ""
        return self.url_base + self.url_path.format(search_term=quote_plus(search_term))

    @sleep_and_retry
    @limits(calls=1, period=10)
    def get_html(self, url=None) -> str:
        self.main_logger.info(f"Sending get request to: {url} using proxy: ")
        header = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/42.0.2311.135 Safari/537.36 Edge/12.246",
        }
        request = requests.get(url, headers=header, proxies=self.proxypool.get_proxy())
        self.search_html = request.text
        self.main_logger.info("Received remote html response")
        self.block_check()
        return self.search_html

    def find_search_result_urls(self) -> list:
        """Searches for URLs in the search results."""
        raise NotImplementedError

    def get_n_text_matches(self, text: str, n: int) -> list:
        raise NotImplementedError
