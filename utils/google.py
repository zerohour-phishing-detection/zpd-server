from requests_html import HTMLResponse, HTMLSession

from utils.logging import main_logger

BLOCK_STR = "Our systems have detected unusual traffic from your computer network. This page checks to see if it's really you sending the requests, and not a robot. Why did this happen?"

logger = main_logger.getChild('utils.google')

def accept_all_cookies(htmlsession: HTMLSession):
    # Send cookie consent POST request, cookies will be stored in session object
    cookie_request_data = {
        "gl": "NL",
        "m": "0",
        "app": "0",
        "pc": "l",
        "continue": "https://google.com/",
        "x": "6",
        "bl": "boq_identityfrontenduiserver_20240225.08_p0",
        "hl": "nl",
        "src": "1",
        "cm": "2",
        "set_sc": "true",
        "set_aps": "true",
        "set_eom": "false",
    }
    html_res = htmlsession.post(
        "https://consent.google.com/save", data=cookie_request_data, allow_redirects=False
    )

    # Check if the HTML response is as expected
    if str(html_res.status_code)[0] != "3":
        # If status code wasn't a redirect
        logger.error("Cookie accept request did not return expected status code!")
        return

    if len(html_res.cookies) == 0:
        logger.error("Cookie accept request did not contain any cookies!")
        return

    # Check if the default 2 cookies are present, warn if not
    if "SOCS" not in html_res.cookies or "NID" not in html_res.cookies:
        logger.warning(
            "Received Google cookies do not contain expect `SOCS` and `NID` cookies, so search queries may return a cookie consent request page instead"
        )

    logger.debug(f"Received cookies: {html_res.cookies}")


def check_blockage(html_res: HTMLResponse):
    """
    Check if we've been temporarily blocked by Google, raising an exception if so.

    Parameters
    ----------
    html_res: HTMLResponse
        The HTML response to detect blockage in.
    """
    if BLOCK_STR in html_res.text:
        raise Exception("Google request was detected by Google bot detection")
