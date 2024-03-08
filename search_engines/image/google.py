import cv2
import numpy as np
from requests_html import HTML, HTMLResponse, HTMLSession

from search_engines.image.base import ReverseImageSearchEngine
from utils.google import accept_all_cookies, check_blockage

API_ENDPOINT = (
    "https://lens.google.com/v3/upload?hl=nl&re=df&st=1709288673579&vpw=790&vph=738&ep=gisbubb"
)
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"

SEARCH_RESULT_SELECTOR = ".Vd9M6 a"


class GoogleReverseImageSearchEngine(ReverseImageSearchEngine):
    """A :class:`ReverseImageSearchEngine` configured for google.com"""

    htmlsession: HTMLSession = None

    def __init__(self):
        super().__init__("Google")

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
        self.create_htmlsession()

        # Encode multipart data
        png_img = cv2.imencode(".png", region)[1]
        multipart_data = {"encoded_image": ("temp.png", png_img, "image/png")}

        # Add User Agent header
        headers = {"user-agent": USER_AGENT}

        self.logger.info("Sending request to Google Lens")
        try:
            # Make POST request
            html_res: HTMLResponse = self.htmlsession.post(
                API_ENDPOINT, files=multipart_data, headers=headers
            )

            if html_res.status_code != 200:
                self.logger.error(f"Google Lens returned status code {html_res.status_code}")
        except Exception as e:
            raise IOError("Error while sending request to Google Lens") from e

        check_blockage(html_res)

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
            raise ValueError(
                "Given HTML wasn't in a known search result format, as no search results were found."
            )

        for match in matches:
            found_urls += match.absolute_links

        return found_urls

    def create_htmlsession(self):
        """
        Creates an `HTMLSession` in `self.htmlsession` and initializes it with cookies.
        """
        if self.htmlsession is not None:
            return

        self.logger.info("Starting HTML session")
        htmlsession = HTMLSession()

        accept_all_cookies(htmlsession)

        self.htmlsession = htmlsession

    def query(self, region: np.ndarray) -> list[str]:
        """
        Performs a reverse image search query for the given region.

        Parameters
        ----------
        region: np.ndarray
            The image as region data to search.

        Returns
        -------
        list[str]
            The result URL strings.
        """
        # Execute search query
        html_res = self.make_request(region)

        html = html_res.html

        # Extract URLs from query results
        extracted_urls = self.extract_search_result_urls(html)

        self.logger.info(
            f"Reverse image search query gave {len(extracted_urls)} results so far"
        )

        return extracted_urls
