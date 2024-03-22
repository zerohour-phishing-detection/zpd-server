import hashlib
import itertools
import os

import joblib
from requests_html import HTMLSession

import utils.classifiers as cl
from logo_finders.reverse_logo_region_search import ReverseLogoRegionSearch
from logo_finders.vision_logo_detection import VisionLogoDetection
from methods import DetectionMethod
from search_engines.image.google import GoogleReverseImageSearchEngine
from search_engines.text.google import GoogleTextSearchEngine
from utils import domains
from utils.async_threads import FutureGroup, ThreadWorker
from utils.logging import main_logger
from utils.result import ResultType
from utils.screenshot import screenshotter
from utils.timing import TimeIt

# Where to store temporary session files, such as screenshots
SESSION_FILE_STORAGE_PATH = "files/"

# Page loading timeout for web driver
WEB_DRIVER_PAGE_LOAD_TIMEOUT = 5

# Which logo finder to use, 1 for `reverse_logo_region_search`, 2 for `vision_logo_detection`
LOGO_FINDER = 2


# Thread worker instance shared for different concurrent parts
worker = ThreadWorker()

# Instantiate a logger for this detection method
logger = main_logger.getChild('methods.dst')

# The HTTP + HTML session to use for reverse image search
html_session = HTMLSession()
html_session.browser  # TODO why is this here

# The logo classifier, deserialized from file
logo_classifier = joblib.load("saved-classifiers/gridsearch_clf_rt_recall.joblib")


class DST(DetectionMethod):
    async def run(self, url, screenshot_url, uuid, pagetitle, image64 = "") -> ResultType:
        url_domain = domains.get_hostname(url)
        url_registered_domain = domains.get_registered_domain(url_domain)

        url_hash = hashlib.sha256(url.encode("utf-8")).hexdigest()

        session_file_path = os.path.join(SESSION_FILE_STORAGE_PATH, url_hash)

        with TimeIt("taking screenshot of " + url):
            # Take screenshot of requested page
            screenshot_path = os.path.join(session_file_path, 'screen.png')
            try:
                screenshotter.save_screenshot(screenshot_url, screenshot_path)
            except Exception as e:
                logger.exception(f"Error taking screenshot: {e}")
                return ResultType.INCONCLUSIVE

        # Perform text search of the screenshot
        with TimeIt("text-only reverse page search"):
            # Initiate text-only reverse image search instance
            search_engine = GoogleTextSearchEngine()
            url_list_text = list(itertools.islice(search_engine.query(pagetitle), 7))

            # Get all unique domains from URLs
            domain_list_text = set([domains.get_hostname(url) for url in url_list_text])

            main_logger.info(f'Found {len(url_list_text)} URLs ({len(domain_list_text)} unique domains)')
            main_logger.debug(f'URLs found: {url_list_text}')
            main_logger.debug(f'domains found: {domain_list_text}')

            # Handle results of search from above
            if await check_search_results(url_registered_domain, domain_list_text, worker):
                logger.info(
                    f"[RESULT] Not phishing, for url {url}, due to registered domain validation from text search"
                )

                # return ResultType.LEGITIMATE

        with TimeIt("image-only reverse page search"):
            if LOGO_FINDER == 1:
                logo_finder = ReverseLogoRegionSearch(
                    reverse_image_search_engines=[GoogleReverseImageSearchEngine()],
                    htmlsession=html_session,
                    clf=logo_classifier
                )
            else:
                logo_finder = VisionLogoDetection()

            async def search_images():
                urls = []
                async for url in logo_finder.find(os.path.join(session_file_path, 'screen.png')):
                    urls.append(url)
                return urls
            url_list_img = await search_images()

            # Get all unique non-checked domains from URLs
            domain_list_img = set([domains.get_hostname(url) for url in url_list_img])
            domain_list_img = domain_list_img.difference(domain_list_text) # remove all domains we already checked

            main_logger.info(f'Found {len(url_list_img)} URLs ({len(domain_list_img)} unique domains)')
            main_logger.debug(f'URLs found: {url_list_img}')
            main_logger.debug(f'domains found: {domain_list_img}')

            # Handle results
            if await check_search_results(url_registered_domain, domain_list_img, worker):
                logger.info(
                    f"[RESULT] Not phishing, for url {url}, due to registered domain validation from reverse image search"
                )

                return ResultType.LEGITIMATE
        
        # No match through images, go on to image comparison per URL
        with TimeIt("image comparisons"):
            out_dir = os.path.join("compare_screens", url_hash)

            future_group: FutureGroup = worker.new_future_group()

            # Check all found URLs
            for index, resulturl in enumerate(url_list_text + url_list_img):
                future_group.schedule(lambda: check_image(out_dir, index, session_file_path, resulturl) == ResultType.PHISHING)
                    
            if future_group.any(id): # Match for found images, so conclude as phishing
                logger.info(f"[RESULT] Phishing, for url {url}, due to image comparisons with index {index}: {resulturl}")
                future_group.cancel()
                return ResultType.PHISHING

        # If the inconclusive stems from google blocking:
        #   e.g. blocked == True
        #   result: inconclusive_blocked

        logger.info(f"[RESULT] Inconclusive, for url {url}")

        worker.close()
        return ResultType.INCONCLUSIVE


def check_image(out_dir, index, session_file_path, resulturl):
    path_a = os.path.join(session_file_path, "screen.png")
    path_b = os.path.join(out_dir, f'{index}.png')
      
    # Take screenshot of URL and save it
    try:
        screenshotter.save_screenshot(resulturl, path_b)
    except Exception as e:
        logger.warning(f"Error taking screenshot of {resulturl}: {str(e)}")
        return False


    # Image compare
    emd, s_sim = None, None
    try:
        emd = cl.earth_movers_distance(path_a, path_b)
    except Exception:
        logger.exception("Error calculating earth_movers_distance")

    try:
        s_sim = cl.structural_sim(path_a, path_b)
    except Exception:
        logger.exception("Error calculating structural_sim")

    logger.info(f"Compared url '{resulturl}'")
    logger.info(f"Finished comparing:  emd = '{emd}', structural_sim = '{s_sim}'")

    if ((emd < 0.001) and (s_sim > 0.70)) or ((emd < 0.002) and (s_sim > 0.80)):
        return True

    return False


async def check_search_results(url_registered_domain, found_domains, worker: ThreadWorker) -> bool:
    with TimeIt("SAN domain check"):
        future_group: FutureGroup = worker.new_future_group()

        for domain in found_domains:
            future_group.schedule(lambda: check_url(url_registered_domain, domain))

        return future_group.any(id)


def check_url(url_registered_domain, domain) -> bool:
    # Get the Subject Alternative Names (all associated domains, e.g. google.com, google.nl, google.de) for all websites
    try:
        san_names = domains.get_san_names(domain)
    except Exception as e:
        logger.error(f"Error in SAN for {domain}: {str(e)}")
        return

    logger.debug(f"Domain {domain} has SAN names {san_names}")

    for hostname in [domain] + san_names:
        # Check if any of the domains found matches the input domain
        registered_domain = domains.get_registered_domain(hostname)
        if url_registered_domain == registered_domain:
            return True
    return False
