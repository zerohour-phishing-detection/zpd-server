import base64

import cv2
import numpy
from bs4 import BeautifulSoup
from ratelimit import limits, sleep_and_retry

from . import ReverseImageSearchEngine


class BingReverseImageSearchEngine(ReverseImageSearchEngine):
    search_start = 0
    next_url = None
    session = None
    retries = 15

    def __init__(self):
        super(BingReverseImageSearchEngine, self).__init__(
            url_base="https://bing.com",
            url_path="/search?q={search_term}",
            url_path_upload="/images/search?view=detailv2&iss=sbiupload&FORM=SBIHMP&sbisrc=ImgPicker&idpbck=1",
            name="Bing",
        )

    @sleep_and_retry
    @limits(calls=1, period=15)
    def get_html(self, url=None) -> str:
        if url is None:
            raise ValueError("No url defined and no prev url available!")

        self.main_logger.info(f"Sending request to: {url}")

        self.search_html = None
        for i in range(self.retries):
            if not self.search_html:
                try:
                    self.main_logger.info(f"Sending get request, attempt: {i}")
                    r = self.session.get(url)
                    r.html.render(timeout=4.0)
                    self.search_html = r.html
                    r.close()
                    self.main_logger.info(f"Status code: {r.status_code}")
                except Exception:
                    self.main_logger.exception(f"Exception while sending GET request to {url}")
            else:
                break

        if not self.search_html:
            self.main_logger.error(f"max tries exceeded and no html response for: {url}")
            return False

        self.main_logger.debug("Received remote HTML response")

        return self.search_html

    def find_search_result_urls(self) -> list:
        if not self.search_html:
            if not self.search_url:
                raise ValueError("No html given yet!")
            if not self.get_html(self.search_url):
                raise ValueError("No html retrieved")

        full_linkset = []

        matches = self.search_html.find("#b_results .b_algo a")
        for match in matches:
            for link in match.absolute_links:
                full_linkset.append(link)
        return full_linkset

    @sleep_and_retry
    @limits(calls=1, period=15)
    def post_html(self, url=None, region=None):
        if not url:
            if not self.search_url:
                raise ValueError("No url defined and no last_searched_url available!")
            url = self.search_url

        multipart = None

        if region is not None:
            if type(region) is numpy.ndarray:
                multipart = {"imageBin": (base64.b64encode(cv2.imencode(".jpg", region)[1]))}
            else:
                raise NotImplementedError()

        self.search_html = None
        for i in range(self.retries):
            if not self.search_html:
                try:
                    self.main_logger.info(f"Sending post request, attempt: {i}")

                    r = self.session.post(url, files=multipart)
                    r.html.render(timeout=4.0)
                    self.main_logger.info(f"Search URL is {r.url}")
                    self.search_html = r.html
                    r.close()

                    self.main_logger.info(f"Status code: {r.status_code}")
                except Exception as err:
                    self.main_logger.warning(f"{err}")
                    pass
            else:
                break
        self.current = None

        return self.search_html

    def result_count(self, default=10) -> int:
        return default

    @sleep_and_retry
    @limits(calls=1, period=15)
    def get_next_results(self):
        if not self.search_html:
            raise ValueError("HTML must be retrieved before result count can be parsed")
        soup = BeautifulSoup(self.search_html.html, "html.parser")
        res = soup.find("div", id="pnnext")
        # Catch not finding the next button
        if not res:
            res = soup.find("a", id="pnnext")
            if not res:
                return False
        next_link = self.url_base + res["href"]
        self.get_html(next_link)
        return True

    @sleep_and_retry
    @limits(calls=1, period=15)
    def get_n_image_matches(self, htmlsession, region, n: int) -> list:
        self.main_logger.info("Starting browser session")
        self.session = htmlsession
        self.post_html(url=self.get_upload_link(), region=region)
        r = self._handle_search(n)
        self.main_logger.info("Ending browser session")
        # self.session.close()
        return r

    @sleep_and_retry
    @limits(calls=1, period=15)
    def get_n_text_matches(self, htmlsession, text: str, n: int) -> list:
        self.main_logger.info("Starting browser session")
        self.session = htmlsession
        self.get_html(url=self.get_search_link_by_terms(text))
        r = self._handle_search(n)
        self.main_logger.info("Ending browser session")
        # self.session.close()
        return r

    @sleep_and_retry
    @limits(calls=1, period=15)
    def _handle_search(self, n):
        results = self.find_search_result_urls()
        cnt = self.result_count()
        self.main_logger.info(f"Found {len(results)} initial results.")
        while len(results) < min(n, cnt):
            self.main_logger.info(f"Extending results due to {len(results)} < {min(n, cnt)}")
            inc = []
            if self.get_next_results():
                inc = self.find_search_result_urls()
            else:
                self.main_logger.info("Extending results failed due to no next button.")
                break
            # Failsafe incase we somehow cant find more results
            if len(inc) == 0:
                self.main_logger.warning("Extending results failed due to no increment.")
                break
            self.main_logger.info(
                f"Found {len(inc)} additional results, totaling to: {len(results) + len(inc)}"
            )
            results += inc
        if len(results) > n:
            results = results[0:n]
        self.main_logger.info(f"{self.name} - Found: {len(results)} links.")
        for res in results:
            self.main_logger.info(f"{res}")
        return results
