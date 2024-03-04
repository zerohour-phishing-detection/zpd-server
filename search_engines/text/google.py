import time
from urllib.parse import parse_qs, urlparse

from bs4 import BeautifulSoup
from ratelimit import limits, sleep_and_retry
from requests_html import HTML, HTMLResponse, HTMLSession

import utils.utils as ut
from search_engines.text.base import TextSearchEngine

BLOCK_STR = "Our systems have detected unusual traffic from your computer network. This page checks to see if it's really you sending the requests, and not a robot. Why did this happen?"
BLOCK_MAX = 5
BLOCK_TIMEOUT = 3600

DEFAULT_RENDER_TIMEOUT = 3.0

class GoogleReverseImageSearchEngine(TextSearchEngine):
    """A :class:`ReverseImageSearchEngine` configured for google.com"""

    session: HTMLSession = None
    blocked_count = 0
    blocked_time_last = 0

    def __init__(self):
        super().__init__('Google')

    def block_check(self):
        """
        Check if we've been temporarily blocked by Google.

        Checks using the last made HTML GET requests, from `self.search_html`.
        Will timeout in case we are blocked.
        """
        if not self.search_html:
            return

        # Reset stats if 30min passed without a block
        if (time.time() - self.blocked_time_last) < 1800:
            self.blocked_count = 0
            self.blocked_time_last = 0

        if BLOCK_STR in self.search_html.text:
            self.blocked_count += 1
            self.blocked_time_last = time.time()

            if self.blocked_count >= BLOCK_MAX:
                self.main_logger.error(
                    f"Blocked too many times by {self.name}. Pausing for {BLOCK_TIMEOUT} seconds."
                )
                ut.to_file("status.txt", "Blocked - Paused")
                
                time.sleep(BLOCK_TIMEOUT)
            else:
                self.main_logger.error(
                    f"Blocked by {self.name} ({self.blocked_count}/{BLOCK_MAX} of long timeout). Pausing for {BLOCK_TIMEOUT / 100} seconds."
                )
                
                time.sleep(BLOCK_TIMEOUT / 100)

    @sleep_and_retry
    @limits(calls=1, period=15)
    def get_html(self, url: str) -> 'HTML':
        """Sends an HTML GET request to the given URL and renders it.

        Parameters
        ----------
        url: str
            The URL to send a GET request to.
        
        Returns
        -------
        requests_html.HTML
            The HTML instance from the response body of the GET request.
            Also stored in `self.search_html`.
        """
        if url is None:
            raise ValueError("No URL given")

        self.main_logger.info(f"Sending GET request to: {url}")

        self.search_html = None
        
        try:
            # Make GET request
            r: HTMLResponse = self.session.get(url)
            
            # Render (run JavaScript code in returned website) and store HTML
            html = r.html
            html.render(timeout=DEFAULT_RENDER_TIMEOUT)

            self.search_html = r

            self.main_logger.info(
                f"Status code: {r.status_code} from URL {r.url}"
            )
        except Exception:
            self.main_logger.exception("Error while sending GET request to Google")
            return None

        self.main_logger.debug("Received remote HTML response")
        self.block_check()

        return self.search_html

    def check_internal_url(self, url: str) -> bool:
        """
        Check if a URL is a Google internal URL.

        Returns
        -------
        bool
            `True` if the URL is usable for filtering, or `False`
            if it's from Google internally.
        """
        parsed_url = urlparse(url)
        netloc = parsed_url.netloc
        query = parsed_url.query
        path = parsed_url.path

        # TODO: this may filter out other websites too (e.g. webcache.googleusercontent.mycoolwebsite.com)
        #         is that an issue?

        # No googleusercontent
        if netloc.startswith("webcache.googleusercontent."):
            return False

        # Filter out the related searches suggestion
        if netloc.startswith("www.google.") and query.startswith("q=related:"):
            return False

        # No cached images
        if netloc == "www.google.com" and path == "imgres":
            return False

        # No Google Translate
        if netloc.startswith("translate.google."):
            return False

        return True

    def find_search_result_urls(self) -> list[str]:
        """
        Searches for URLs in the search results.

        Looks through `self.search_html` for search result URLs,
        possibly first fetching the search results using `self.search_url`.
        """
        if not self.search_html:
            if not self.search_url:
                raise ValueError("No HTML or URL given")
            # No search HTML present yet, try fetching it
            if not self.get_html(self.search_url):
                raise ValueError("No HTML was retrieved from URL")

        found_urls = []

        # New text search
        matches = self.search_html.find(".egMi0.kCrYT")
        for match in matches:
            for link in match.absolute_links:
                # Google has these redirect links, extract the direct link from it in the query parameters
                url = urlparse(link)
                qs = parse_qs(url.query)
                if "url" not in qs:
                    continue
                new_link = qs["url"][0]

                # Verify URL and add it
                if self.check_internal_url(new_link):
                    found_urls.append(new_link)

        return found_urls

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
    def get_n_text_matches(self, htmlsession, text: str, n: int) -> list:
        self.main_logger.info("Starting browser session")

        self.session = htmlsession
        self.get_html(url=self.get_search_link_by_terms(text))
        r = self._handle_search(n)

        self.main_logger.info("Ending browser session")

        return r

    @sleep_and_retry
    @limits(calls=1, period=15)
    def _handle_search(self, n):
        results = self.find_search_result_urls()
        cnt = self.result_count(default=10)

        self.main_logger.info(f"Found {len(results)} initial results.")

        while len(results) < min(n, cnt):
            self.main_logger.info(
                f"Extending results due to {len(results)} < {min(n, cnt)}"
            )
            inc = []
            if self.get_next_results():
                inc = self.find_search_result_urls()
            else:
                self.main_logger.info("Extending results failed due to no next button.")
                break

            # Failsafe incase we somehow cant find more results
            if len(inc) == 0:
                self.main_logger.warning(
                    "Extending results failed due to no increment."
                )
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