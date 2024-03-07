from typing import Iterator
from urllib.parse import parse_qs, quote_plus, urlparse

from requests_html import HTML, HTMLResponse, HTMLSession

from search_engines.text.base import TextSearchEngine
from utils.google import accept_all_cookies, check_blockage

SEARCH_RESULT_SELECTOR = ".egMi0.kCrYT"
NEXT_PAGE_SELECTOR = ".nBDE1b.G5eFlf"

# TODO improve cookie page detection


class GoogleTextSearchEngine(TextSearchEngine):
    """A :class:`TextSearchEngine` configured for google.com"""

    htmlsession: HTMLSession = None

    def __init__(self):
        super().__init__("Google")

    def construct_search_url(self, query: str) -> str:
        """
        Constructs the search query URL given a text query.
        """
        return "https://www.google.com/search?q=" + quote_plus(query)

    def make_request(self, url: str) -> HTMLResponse:
        """Sends an HTML GET request to the given URL.

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

        self.logger.info(f"Sending request to: {url}")

        try:
            # Make GET request
            html_res: HTMLResponse = self.htmlsession.get(url)

            self.logger.info(f"Request returned status code: {html_res.status_code}")
        except Exception as e:
            raise IOError(f"Error while sending request to Google to URL `{url}`") from e

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
            if "heeft geen overeenkomstige documenten opgeleverd" in html.text:
                return []

            raise ValueError(
                "Given HTML wasn't in a known search result format, as no search results were found."
            )

        for match in matches:
            for link in match.absolute_links:
                # Google has these redirect links, extract the direct link from it in the query parameters
                url = urlparse(link)
                qs = parse_qs(url.query)
                if "url" not in qs:
                    continue
                new_link = qs["url"][0]

                # Verify URL and add it
                found_urls.append(new_link)

        return found_urls

    def get_next_page_link(self, html: HTML, first_page=True) -> str | None:
        """
        Obtains the URL for the next page of search results from the given `HTML`.

        Returns
        -------
        str or None
            The URL for the page containing the next search results,
            or None if no next page is available.
        """
        # First, use CSS selector to find next page button
        matches = html.find(NEXT_PAGE_SELECTOR)

        if (first_page and len(matches) != 1) or (not first_page and len(matches) != 2):
            if len(matches) == 0:
                self.logger.warning(
                    "Could not find next page button in `HTML` object, either indicative of no search results or of Google interface changes"
                )
            return None

        # Allow either 1 (next page button) or 2 (previous page + next page) a elements.
        # Always get the first element, as it is next page.

        # Extract absolute link(s) from that button
        links = matches[0].absolute_links
        if len(links) != 1:
            raise ValueError(f"Next page button has non-one links (it has {len(links)}): {links}")

        # Return the absolute link
        return list(links)[0]

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

    def query(self, text: str) -> Iterator[str]:
        """
        Performs a text search query for the given text.

        Parameters
        ----------
        text: str
            The text to perform the query for.

        Yields
        ------
        str
            The result URL string.
        """
        # Construct initial search query URL
        url = self.construct_search_url(text)
        first_page = True
        while True:
            # Execute search query
            html_res = self.make_request(url)
            html = html_res.html

            # Extract URLs from query results
            extracted_urls = self.extract_search_result_urls(html)

            if len(extracted_urls) == 0:
                break

            self.logger.info(f"Text search query gave {len(extracted_urls)} results so far")

            # Yield all retrieved URLs
            yield from extracted_urls

            # Continue on with the results from the next page
            url = self.get_next_page_link(html, first_page=first_page)
            if url is None:
                break

            first_page = False

            self.logger.info(f"Visiting next page with URL `{url}`")

        self.logger.info("Text search query reached end")
