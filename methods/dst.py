import asyncio
import concurrent.futures
import hashlib
import os
import sqlite3

import joblib
from requests_html import HTMLSession
from selenium import webdriver
from selenium.webdriver.chrome.options import Options

import utils.classifiers as cl
from methods import DetectionMethod
from parsing import Parsing
from search_engines.image.google import GoogleReverseImageSearchEngine
from search_engines.text.google import GoogleTextSearchEngine
from utils import domains
from utils.custom_logger import main_logger
from utils.result import ResultType
from utils.reverse_image_search import ReverseImageSearch
from utils.timing import TimeIt

# Option for saving the taken screenshots
SAVE_SCREENSHOT_FILES = False
# Whether to use the Clearbit logo API (see https://clearbit.com/logo)
USE_CLEARBIT_LOGO_API = False

# Where to store temporary session files, such as screenshots
SESSION_FILE_STORAGE_PATH = "files/"
# Database path for the operational output (?)
DB_PATH_OUTPUT = "db/output_operational.db"
# Database path for the sessions

# Page loading timeout for web driver
WEB_DRIVER_PAGE_LOAD_TIMEOUT = 5


# The main logger for the whole program, singleton
logger = main_logger.getChild('methods.dst')

# The HTTP + HTML session to use for reverse image search
html_session = HTMLSession()
html_session.browser  # TODO why is this here

# The logo classifier, deserialized from file
logo_classifier = joblib.load("saved-classifiers/gridsearch_clf_rt_recall.joblib")


class DST(DetectionMethod):
    def run(self, url, screenshot_url, uuid, pagetitle, image64 = "") -> ResultType:
        url_domain = domains.get_hostname(url)
        url_registered_domain = domains.get_registered_domain(url_domain)

        url_hash = hashlib.sha256(url.encode("utf-8")).hexdigest()

        session_file_path = os.path.join(SESSION_FILE_STORAGE_PATH, url_hash)

        with TimeIt("taking screenshot"):
            # Take screenshot of requested page
            parsing = Parsing(
                SAVE_SCREENSHOT_FILES,
                pagetitle,
                image64,
                screenshot_url,
                store=session_file_path,
            )
            screenshot_width, screenshot_height = parsing.get_size()

        db_conn_output = sqlite3.connect(DB_PATH_OUTPUT)

        # Perform text search of the screenshot
        with TimeIt("text-only reverse page search"):
            # Initiate text-only reverse image search instance
            search = ReverseImageSearch(
                storage=DB_PATH_OUTPUT,
                reverse_image_search_engines=[GoogleReverseImageSearchEngine()],
                text_search_engines=[GoogleTextSearchEngine()],
                folder=SESSION_FILE_STORAGE_PATH,
                upload=False,
                mode="text",
                htmlsession=html_session,
                clf=logo_classifier,
            )

            search.handle_folder(session_file_path, url_hash)

            # Get result from the above search
            url_list_text = db_conn_output.execute(
                "SELECT DISTINCT result FROM search_result_text WHERE filepath = ?",
                [url_hash],
            ).fetchall()
            url_list_text = [url[0] for url in url_list_text]

            # Handle results of search from above
            if asyncio.run(check_search_results(url_registered_domain, url_list_text)):
                logger.info(
                    f"[RESULT] Not phishing, for url {url}, due to registered domain validation"
                )

                return ResultType.LEGITIMATE

        with TimeIt("image-only reverse page search"):
            search = ReverseImageSearch(
                storage=DB_PATH_OUTPUT,
                reverse_image_search_engines=[GoogleReverseImageSearchEngine()],
                text_search_engines=[GoogleTextSearchEngine()],
                folder=SESSION_FILE_STORAGE_PATH,
                upload=True,
                mode="image",
                htmlsession=html_session,
                clf=logo_classifier,
                clearbit=USE_CLEARBIT_LOGO_API,
                tld=url_registered_domain,
            )
            search.handle_folder(session_file_path, url_hash)

            # Get results from above search
            url_list_img = db_conn_output.execute(
                "SELECT DISTINCT result FROM search_result_image WHERE filepath = ?",
                [url_hash],
            ).fetchall()
            url_list_img = [url[0] for url in url_list_img]

            # Handle results
            if asyncio.run(check_search_results(url_registered_domain, url_list_img)):
                logger.info(
                    f"[RESULT] Not phishing, for url {url}, due to registered domain validation"
                )

                return ResultType.LEGITIMATE

        # No match through images, go on to image comparison per URL
        with TimeIt("image comparisons"):
            out_dir = os.path.join("compare_screens", url_hash)
            if not os.path.exists(out_dir):
                os.makedirs(out_dir)

            # Initialize web driver
            options = Options()
            options.add_argument("--headless")

            driver = webdriver.Chrome(options=options)
            driver.set_window_size(screenshot_width, screenshot_height)
            driver.set_page_load_timeout(WEB_DRIVER_PAGE_LOAD_TIMEOUT)

            # Check all found URLs
            for index, resulturl in enumerate(url_list_text + url_list_img):
                if check_image(driver, out_dir, index, session_file_path, resulturl):
                    # Match for found images, so conclude as phishing
                    driver.quit()

                    logger.info(f"[RESULT] Phishing, for url {url}, due to image comparisons")

                    return ResultType.PHISHING
            driver.quit()

        # If the inconclusive stems from google blocking:
        #   e.g. blocked == True
        #   result: inconclusive_blocked

        logger.info(f"[RESULT] Inconclusive, for url {url}")

        return ResultType.INCONCLUSIVE


def check_image(driver, out_dir, index, session_file_path, resulturl):
    # Take screenshot of URL and save it
    try:
        driver.get(resulturl)
    except Exception:
        return False
    driver.save_screenshot(out_dir + "/" + str(index) + ".png")

    # Image compare
    path_a = os.path.join(session_file_path, "screen.png")
    path_b = out_dir + "/" + str(index) + ".png"

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


async def check_search_results(url_registered_domain, found_urls) -> bool:
    with TimeIt("SAN domain check"):
        with concurrent.futures.ThreadPoolExecutor() as pool:
            loop = asyncio.get_running_loop()
            coros = []
            for url in found_urls:
                coros.append(
                    loop.run_in_executor(pool, lambda: check_url(url_registered_domain, url))
                )

            for coro in asyncio.as_completed(coros):
                if await coro:
                    return True

        # If no match, no results yet
        return False


def check_url(url_registered_domain, url) -> bool:
    # For each found URL, get the hostname
    domain = domains.get_hostname(url)

    # Get the Subject Alternative Names (all associated domains, e.g. google.com, google.nl, google.de) for all websites
    try:
        san_names = domains.get_san_names(domain)
    except Exception:
        logger.error(f"Error in SAN for {domain} (from URL {url})", exc_info=1)
        return

    logger.debug(f"Domain of URL `{url}` is {domain}, with SAN names {san_names}")

    for hostname in [domain] + san_names:
        # Check if any of the domains found matches the input domain
        registered_domain = domains.get_registered_domain(hostname)
        if url_registered_domain == registered_domain:
            return True
    return False
