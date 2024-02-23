import time

from urllib.parse import urlparse, parse_qs
from ratelimit import limits, sleep_and_retry

from requests_html import HTMLSession
from bs4 import BeautifulSoup
from . import ReverseImageSearchEngine

import cv2
import numpy
from skimage.io import imread

import utils.utils as ut

class GoogleReverseImageSearchEngine(ReverseImageSearchEngine):
    """A :class:`ReverseImageSearchEngine` configured for google.com
    """
    search_start = 0
    next_url = None
    session: HTMLSession = None
    # default 1
    retries = 1
    block_cnt = 0
    block_time = 0
    block_max = 5
    block_timeout = 3600
    # default render timeout for r.html.render(timeout=3.0) = 3 sec

    def __init__(self):
        super(GoogleReverseImageSearchEngine, self).__init__(
            url_base='http://www.google.com',
            url_path='/search?q={search_term}',
            url_path_upload='/searchbyimage/upload',
            name='Google'
        )

    def block_check(self) -> bool:
        if not self.search_html:
            return False

        # Reset stats if 30min passed without a block
        if (time.time() - self.block_time) < 1800:
            self.block_cnt = 0
            self.block_time = 0

        block_str = "Our systems have detected unusual traffic from your computer network. This page checks to see if it's really you sending the requests, and not a robot. Why did this happen?"
        if (block_str in self.search_html.text):
            self.block_cnt += 1
            self.block_time = time.time()

            if self.block_cnt >= self.block_max:
                self.main_logger.error(f"Blocked too many times by {self.name}. Pausing for {self.block_timeout} seconds.")
                ut.toFile("status.txt", f"Blocked - Paused")
                time.sleep(self.block_timeout)
            else:
                self.main_logger.error(f"Blocked by {self.name} ({self.block_cnt}/{self.block_max} of long timeout). Pausing for {self.block_timeout/100} seconds.")
                time.sleep(self.block_timeout/100)
        return False

    @sleep_and_retry
    @limits(calls=1, period=15)
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
                    r.html.render(timeout=3.0)
                    
                    self.search_html = r.html
                    
                    r.close()
                    
                    self.main_logger.info(f"Status code: {r.status_code} from URL {r.url}")
                except Exception as err:
                    self.main_logger.warning(f"{err}")
                    pass
            else:
                break

        if not self.search_html:
            self.main_logger.error(f"max tries exceeded and no html response for: {url}")
            return False

        self.main_logger.debug('Received remote HTML response')
        self.block_check()

        return self.search_html

    def verify_url(self, urlstr: str) -> bool:
        url = urlparse(urlstr)
        if url.netloc.startswith('webcache.googleusercontent.'):
            return False
        elif url.netloc.startswith('www.google.') and url.query.startswith('q=related:'):
            return False
        elif urlstr.startswith('https://www.google.com/imgres?'):
            return False
        elif url.netloc.startswith('translate.google.'):
            return False
        else:
            return True

    def find_matches(self) -> list:
        if not self.search_html:
            # self.main_logger.warning(f"DEBUG: {self.search_html}")
            if not self.search_url:
                raise ValueError('No html given yet!')
            if not self.get_html(self.search_url):
                raise ValueError('No html retrieved')

        full_linkset = []
        matches = self.search_html.find('.g .yuRUbf a')
        for match in matches:
            for l in match.absolute_links:
                if self.verify_url(l):
                    full_linkset.append(l)

        matches = self.search_html.find('.g .rc a')
        for match in matches:
            for l in match.absolute_links:
                if self.verify_url(l):
                    full_linkset.append(l)
        
        matches = self.search_html.find('.egMi0.kCrYT')
        for match in matches:
            for l in match.absolute_links:
                url = urlparse(l)
                qs = parse_qs(url.query)
                if 'url' not in qs:
                    continue
                new_link = qs['url'][0]
                if self.verify_url(new_link):
                    full_linkset.append(new_link)

        return full_linkset

    @sleep_and_retry
    @limits(calls=1, period=15)
    def post_html(self, url=None, region=None):
        if not url:
            if not self.search_url:
                raise ValueError('No url defined and no last_searched_url available!')
            url = self.search_url

        multipart = None

        if not (region is None):
            if type(region) is numpy.ndarray:
                multipart = {'encoded_image': ('temp.png', cv2.imencode('.png', region)[1])}
            elif os.path.exists(image):
                multipart = {'encoded_image': (region, open(region, 'rb'))}
            else:
                raise NotImplementedError

        self.search_html = None
        for i in range(self.retries):
            if not self.search_html:
                try:
                    self.main_logger.info(f"Sending post request (to {url}, multipart keys {multipart.keys() if multipart != None else None}), attempt: {i}")
                    
                    r = self.session.post(url, files=multipart)
                    r.html.render(timeout=3.0)
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
        self.block_check()

        return self.search_html

    def result_count(self, default=10) -> int:
        return default

    @sleep_and_retry
    @limits(calls=1, period=15)
    def get_next_results(self):
        if not self.search_html:
            raise ValueError("HTML must be retrieved before result count can be parsed")
        
        soup = BeautifulSoup(self.search_html.html, 'html.parser')
        res = soup.find('div', id='pnnext')
        
        # Catch not finding the next button
        if not res:
            res = soup.find('a', id='pnnext')
            if not res:
                return False
        
        next_link = self.url_base + res['href']
        self.get_html(next_link)
        return True

    @sleep_and_retry
    @limits(calls=1, period=15)
    def get_n_image_matches(self, htmlsession, region, n:int) -> list:
        self.main_logger.info(f"Starting browser session")
        
        self.session = htmlsession
        
        url = self.get_upload_link()
        self.main_logger.info(f"URL: {url}")
        self.post_html(url=url, region=region)
        
        r = self._handle_search(n)
        
        self.main_logger.info(f"Ending browser session")
        return r

    @sleep_and_retry
    @limits(calls=1, period=15)
    def get_n_image_matches_clearbit(self, htmlsession, tld, n:int) -> list:
        self.main_logger.info(f"Starting browser session")
        self.session = htmlsession
        # Get clearbit logo as png as numpy ndarray
        try:
            region = imread(f"https://logo.clearbit.com/{tld}")
            self.main_logger.info(f"https://logo.clearbit.com/{tld}")
            # Region is RGB, but rest is BGR, so convert
            region = region[:,:,::-1]
            
            self.post_html(url=self.get_upload_link(), region=region)
            
            r = self._handle_search(n)
            
            self.main_logger.info(f"Ending browser session")

            return r
        except:
            return None

    @sleep_and_retry
    @limits(calls=1, period=15)
    def get_n_text_matches(self, htmlsession, text:str, n:int) -> list:
        self.main_logger.info(f"Starting browser session")
        
        self.session = htmlsession
        self.get_html(url=self.get_search_link_by_terms(text))
        r = self._handle_search(n)
        
        self.main_logger.info(f"Ending browser session")
        
        return r

    @sleep_and_retry
    @limits(calls=1, period=15)
    def _handle_search(self, n):
        results  = self.find_matches()
        cnt = self.result_count(default=10)
        
        self.main_logger.info(f"Found {len(results)} initial results.")

        while len(results) < min(n, cnt):
            self.main_logger.info(f"Extending results due to {len(results)} < {min(n, cnt)}")
            inc = []
            if self.get_next_results():
                inc = self.find_matches()
            else:
                self.main_logger.info(f"Extending results failed due to no next button.")
                break
            
            # Failsafe incase we somehow cant find more results
            if len(inc) == 0:
                self.main_logger.warning(f"Extending results failed due to no increment.")
                break
            
            self.main_logger.info(f"Found {len(inc)} additional results, totaling to: {len(results) + len(inc)}")
            results += inc
        if len(results) > n:
            results = results[0:n]
        
        self.main_logger.info(f"{self.name} - Found: {len(results)} links.")
        for res in results:
            self.main_logger.info(f"{res}")
        
        return results
