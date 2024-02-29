import logging
from urllib.parse import quote_plus

import requests
from ratelimit import limits, sleep_and_retry
import requests

from utils.proxygetter import ProxyGetter
from utils.customlogger import CustomLogger


class ReverseImageSearchEngine:
    name = "Base"
    logger = logging.getLogger(__name__)
    proxypool = ProxyGetter()

    main_logger = None

    search_html = None
    search_url = None
    url_path_upload = None

    def __init__(self, url_base, url_path, url_path_upload, name=None):
        self.url_base = url_base
        self.url_path = url_path
        self.url_path_upload = url_path_upload
        self.name = name
        self.main_logger = CustomLogger().main_logger

    def get_search_link_by_url(self, url) -> str:
        self.search_url = url
        self.search_html = ""
        return self.url_base + self.url_path.format(image_url=quote_plus(url))

    def get_search_link_by_terms(self, search_term) -> str:
        self.search_html = ""
        return self.url_base + self.url_path.format(search_term=quote_plus(search_term))

    def get_upload_link(self) -> str:
        return self.url_base + self.url_path_upload

    def block_check(self) -> bool:
        return False

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

    def check_image_availability(self, url: str) -> bool:
        try:
            return requests.head(url, proxies=self.proxypool.get_proxy()) == 200
        except Exception:
            return False

    def find_search_result_urls(self) -> list:
        """Searches for URLs in the search results.
        """
        raise NotImplementedError

    def get_n_image_matches(self, region, n: int) -> list:
        raise NotImplementedError

    def get_n_image_matches_clearbit(self, region, n: int) -> list:
        raise NotImplementedError

    def get_n_text_matches(self, text: str, n: int) -> list:
        raise NotImplementedError
