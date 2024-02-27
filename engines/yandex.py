import requests
from bs4 import BeautifulSoup, SoupStrainer
from urllib.parse import urlparse, quote_plus
from . import ReverseImageSearchEngine
import utils.utils as ut
import time
from ratelimit import limits, sleep_and_retry
from utils.proxy_getter import ProxyGetter
from requests_html import HTMLSession

__all__ = ['YandexReverseImageSearchEngine']


class YandexReverseImageSearchEngine(ReverseImageSearchEngine):
    """A :class:`ReverseImageSearchEngine` configured for yandex.com
    """
    session = None
    retries = 15
    proxypool = ProxyGetter()

    def __init__(self):
        super(YandexReverseImageSearchEngine, self).__init__(
            url_base='http://yandex.com',
            url_path='/search/?text={search_term}',
            url_path_upload='/images/search',
            name='Yandex'
        )

    def block_check(self) -> bool:
        if not self.search_html:
            return False
        return False

    @sleep_and_retry
    @limits(calls=1, period=1)
    def translate(self, url:int) -> str:
        self.main_logger.debug(f"Tracing URL: {url}")

        header = {'User-Agent' : 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/42.0.2311.135 Safari/537.36 Edge/12.246',}
        r = requests.get(url, headers=header, proxies=self.proxypool.get_proxy())
        soup = BeautifulSoup(r.text, 'html.parser')
        metatag = soup.find("meta", {"http-equiv":"refresh"})

        # Slicing is to extract url from: 0;URL='www.target.com'
        furl = metatag['content'][7:-1]

        self.main_logger.debug(f"Final URL: {furl}")
        return furl

    @sleep_and_retry
    @limits(calls=1, period=10)
    def get_html(self, url=None) -> str:
        if not url:
            raise ValueError('No url defined and no prev url available!')
        self.main_logger.info(f"Sending request to: {url}")
        self.search_html = None
        for i in range(self.retries):
            if not self.search_html:
                try:
                        self.main_logger.info(f"Sending get request, attempt: {i}")
                        r = self.session.get(url)
                        r.html.render(timeout=40.0)
                        self.search_html = r.html
                        self.main_logger.info(f"Status code: {r.status_code}")
                except Exception as err:
                        self.main_logger.error(f"{err}")
                        pass
                else:
                    break
        self.main_logger.debug('Received remote HTML response')
        self.block_check()
        return self.search_html

    def find_matches(self) -> list:
        if not self.search_html:
            if not self.search_url:
                raise ValueError('No html given yet!')
            self.get_html(self.search_url)

        full_linkset = []
        matches = self.search_html.find('.g .r a')

        for match in matches:
            for l in match.absolute_links:
                if self.verify_url(l):
                    full_linkset.append(l)

        return full_linkset

    @sleep_and_retry
    @limits(calls=1, period=10)
    def post_html(self, url=None, region=None):
        if not url:
            if not self.search_url:
                raise ValueError('No url defined and no last_searched_url available!')
            url = self.search_url

        multipart = None

        if not (region is None):
            if type(region) is numpy.ndarray:
                multipart = {'upfile': ('temp.png', cv2.imencode('.png', region)[1])}
            elif os.path.exists(image):
                multipart = {'upfile': (region, open(region, 'rb'))}
            else:
                raise NotImplementedError

        self.search_html = None
        for i in range(self.retries):
            if not self.search_html:
                try:
                        self.main_logger.info(f"Sending post request, attempt: {i}")
                        r = self.session.post(url, files=multipart)
                        r.html.render(timeout=40.0)
                        self.search_html = r.html
                        self.main_logger.info(f"Status code: {r.status_code}")
                except Exception as err:
                    self.main_logger.error(f"{err}")
                    pass
            else:
                    break
        if r.status_code > 399:
            raise ValueError(f"Blocked by {self.name}, with response code: {r.status_code}")
        self.block_check()

        return self.search_html

    @sleep_and_retry
    @limits(calls=1, period=20)
    def get_n_image_matches(self, region, n:int) -> list:
        if not self.search_html:
            if not self.search_url:
                raise ValueError('No image given yet!')
            self.get_html(self.search_url)

        soup = BeautifulSoup(self.search_html, 'html.parser')
        full_linkset = []
        for link in soup.find_all('a', {'class' : 'other-sites__snippet-title-link'}):
            if link.has_attr('href'):
                full_linkset.append(link['href'])
        self.main_logger.info(f"Translating {self.name}'s internal URL's, this can take a moment.")
        translated_links = []
        for cnt in range(0, min(n, len(full_linkset))):
            translated_links.append(self.translate(full_linkset[cnt]))
        self.main_logger.info(f"{self.name} - Found: {len(translated_links)} links.")
        if len(translated_links) < n:
            self.block_check()
        return translated_links

    @sleep_and_retry
    @limits(calls=1, period=20)
    def get_n_text_matches(self, text:str, n:int) -> list:
        self.main_logger.info(f"Starting browser session")
        self.session = HTMLSession()

        self.get_html(url=self.get_search_link_by_terms(text))
        ut.to_file("resp.html", self.search_html.html)
        soup = BeautifulSoup(self.search_html.html, 'html.parser')
        full_linkset = []
        for link in soup.find_all('a', {'class' : 'organic__url'}):
            if link.has_attr('href'):
                full_linkset.append(link['href'])
        self.main_logger.info(f"{self.name} - Found: {len(full_linkset)} links.")
        if len(full_linkset) < n:
            self.block_check()
        self.main_logger.info(f"Ending browser session")
        self.session.close()

        if len(full_linkset) > n:
            full_linkset = full_linkset[0:n]
        for res in full_linkset:
            self.main_logger.info(f"{res}")
        return full_linkset
