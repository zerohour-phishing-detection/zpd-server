import time
from typing import Iterator

import cv2
from requests_html import HTML, HTMLResponse, HTMLSession

import utils.utils as ut
from search_engines.image.base import ReverseImageSearchEngine

BLOCK_STR = "Our systems have detected unusual traffic from your computer network. This page checks to see if it's really you sending the requests, and not a robot. Why did this happen?"
BLOCK_MAX = 5
BLOCK_TIMEOUT = 3600

DEFAULT_RENDER_TIMEOUT = 3.0

SEARCH_RESULT_SELECTOR = ".Vd9M6 a"

class GoogleReverseImageSearchEngine(ReverseImageSearchEngine):
    """A :class:`ReverseImageSearchEngine` configured for google.com"""

    htmlsession: HTMLSession = None
    blocked_count = 0
    blocked_time_last = 0

    def __init__(self):
        super().__init__('Google')

    def block_check(self, html_res: HTMLResponse):
        """
        Check if we've been temporarily blocked by Google.

        Parameters
        ----------
        html_res: HTMLResponse
            The HTML response to detect blockage in.
        """
        # Reset stats if 30min passed without a block
        if (time.time() - self.blocked_time_last) < 1800:
            self.blocked_count = 0
            self.blocked_time_last = 0

        if BLOCK_STR in html_res.text:
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

    def make_request(self, region) -> HTMLResponse:
        """Sends an HTML POST request to Google Lens with the given region.

        Parameters
        ----------
        url: str
            The URL to send the request to.
        
        Returns
        -------
        requests_html.HTMLResponse
            The HTML response from the request.
        """

        url = "https://lens.google.com/v3/upload?hl=nl&re=df&st=1709288673579&vpw=790&vph=738&ep=gisbubb"
        
        # Encode multipart data
        png_img = cv2.imencode(".png", region)[1]
        multipart_data = {"encoded_image": ("temp.png", png_img, 'image/png')}
        
        # Add User Agent header
        headers = {
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36'
        }

        self.main_logger.info("Sending request to Google Lens")
        try:
            # Make POST request
            html_res: HTMLResponse = self.htmlsession.post(url, files=multipart_data, headers=headers)

            if html_res.status_code != 200:
                self.main_logger.error(f"Google Lens returned status code {html_res.status_code}")
        except Exception as e:
            raise IOError('Error while sending request to Google Lens') from e

        self.block_check(html_res)

        return html_res

    def extract_search_result_urls(self, html: HTML) -> list[str]:
        """
        Searches for URLs in the search results.

        Parameters
        ----------
        html: HTML
            The HTML of the Google page to search through.
        """
        found_urls = []

        # New text search
        matches = html.find(SEARCH_RESULT_SELECTOR)
        if len(matches) == 0:
            raise ValueError("Given HTML wasn't in a known search result format, as no search results were found.")

        for match in matches:
            for link in match.absolute_links:
                # Verify URL and add it
                found_urls.append(link)

        return found_urls

    def create_htmlsession(self):
        """
        Creates an `HTMLSession` in `self.htmlsession` and initializes it with cookies.
        """
        if self.htmlsession is not None:
            return
        
        self.main_logger.info("Starting HTML session")
        htmlsession = HTMLSession()

        # Send cookie consent POST request, cookies will be stored in session object
        cookie_request_data = {
            'gl': 'NL',
            'm': '0',
            'app': '0',
            'pc': 'l',
            'continue': 'https://google.com/',
            'x': '6',
            'bl': 'boq_identityfrontenduiserver_20240225.08_p0',
            'hl': 'nl',
            'src': '1',
            'cm': '2',
            'set_sc': 'true',
            'set_aps': 'true',
            'set_eom': 'false'
        }
        html_res = htmlsession.post('https://consent.google.com/save', data=cookie_request_data, allow_redirects=False)
        # Check if the default 2 cookies are present, warn if not
        if 'SOCS' not in html_res.cookies or 'NID' not in html_res.cookies:
            self.main_logger.warning("Received Google cookies do not contain expect `SOCS` and `NID` cookies, so search queries may return a cookie page instead")
        
        self.main_logger.debug(f"Received cookies: {html_res.cookies}")

        self.htmlsession = htmlsession

    def query(self, region) -> Iterator['str']:
        self.create_htmlsession()

        # Execute search query
        html_res = self.make_request(region)

        html = html_res.html
        
        # Extract URLs from query results
        extracted_urls = self.extract_search_result_urls(html)

        if len(extracted_urls) == 0:
            self.main_logger.info('Reverse image search query reached end')
            return

        self.main_logger.info(f'Reverse image search query gave {len(extracted_urls)} results so far')

        # Yield all retrieved URLs
        for extracted_url in extracted_urls:
            yield extracted_url
