from requests_html import HTMLSession
from flask import Flask, request, jsonify, send_file, send_from_directory, render_template
import hashlib
from collections import defaultdict
import socket
import ssl
import tldextract

from webdriver_manager.chrome import ChromeDriver
from utils.customlogger import CustomLogger
import time
from datetime import datetime
import logging
import os
import searchengine
import signal
from parsing import Parsing
from utils.reverseimagesearch import ReverseImageSearch
from engines.google import GoogleReverseImageSearchEngine
from engines.bing import BingReverseImageSearchEngine
import sqlite3
from urllib.parse import urlparse
from selenium import webdriver
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.options import Options
import utils.classifiers as cl
import joblib
from utils.sessions import Sessions
import utils.appendsandomains as appdom

#to avoid RuntimeError('This event loop is already running') when there are many of requests
import nest_asyncio

main_logger = CustomLogger().main_logger
htmlsession = HTMLSession()
htmlsession.browser

clf_logo = joblib.load('saved-classifiers/gridsearch_clf_rt_recall.joblib')
clientscreen = False	# don't save client screenshot
clearbit = True # set clearbit API on

def_folder = "files/"
def_storage = "db/output_operational.db"
session_db = "db/sessions.db"
sessions = Sessions(session_db, False)

# sets the load page timeout for the web driver
webdriver_timeout = 5

app = Flask(__name__)
app.config["DEBUG"] = False

@app.route('/', methods=['GET'])
def home():
    return render_template('index.html')

@app.route('/stop', methods=['GET'])
def shutdown():
    shutdown_server()
    return 'Server shutting down...'
    
def shutdown_server():
    # func = request.environ.get('werkzeug.server.shutdown')
    # if func is None:
    #     raise RuntimeError('Not running with the Werkzeug Server')
    # func()
    os._exit(0)

@app.route('/api/v1/url', methods=['POST'])
def check_url():
    startTime = time.time()
    json = request.get_json()
    #main_logger.info("Received JSON: " + str(json))
    #main_logger.warn("Received JSON: " + str(json))
    #main_logger.warn("Received JSON: " + str(json["URL"]))
    url = json["URL"]
    uuid = json["uuid"]
    main_logger.info("\n\n\n##########################################################\n##### Request received for URL:\t" + str(url) + "\n##########################################################")

    # extra json field for evaluation purposes
    # the hash computed in the DB is the this one
    if "phish_url" in json:
        url = json["phishURL"]
        main_logger.info("Real URL changed to phishURL: " + str(url) + "\n")
    else:
        main_logger.info("Not a phish URL, real URL") # + str(phish_url)) 	

    urldomain = urlparse(url).netloc

    shahash = hashlib.sha1(url.encode('utf-8')).hexdigest()

    # check is in cache or still processing...
    result = []
    cache_result = sessions.get_state(uuid, url)
#    main_logger.info("Is in cache?" + str(cache_result))
    if cache_result != 'new':
        if cache_result[0] == 'processing':
            time.sleep(4)
        stopTime = time.time()
        main_logger.warn(f"Time elapsed for {url} is {stopTime - startTime}, found in cache with result {cache_result[0]}")
        result.append({'url': url, 'status': cache_result[0], 'sha1': shahash})
        return jsonify(result)
    
    sessions.store_state(uuid, url, 'processing', 'textsearch')

    parse = Parsing(clientscreen, json=json, store="files/" + shahash)
    image_width, image_height = parse.get_size()

    conn_storage = sqlite3.connect(def_storage)

    ######
    textFindST = time.time()
    ######

    search = ReverseImageSearch(storage=def_storage, search_engine=list(GoogleReverseImageSearchEngine().identifiers())[0], folder=def_folder, upload=False, mode="text", htmlsession=htmlsession, clf=clf_logo)
    search.handle_folder(os.path.join(def_folder, shahash), shahash)
    url_list_text = conn_storage.execute("select distinct result from search_result_text WHERE filepath = ?", (shahash,)).fetchall()

    ######
    textFindSPT = time.time()
    main_logger.warn(f"Time elapsed for text find for {shahash} is {textFindSPT - textFindST}")
    sanTextST = time.time()
    ######

    domain_list=[]
    for urls in url_list_text:
        url_domain = urlparse(urls[0]).netloc
        domain_list.append(url_domain)

    domain_list_with_san = domain_list.copy()

    # Get SAN names and append
    for domain in domain_list:
        try:
            context = ssl.create_default_context()
            with socket.create_connection((domain, 443), timeout=2) as sock:
                with context.wrap_socket(sock, server_hostname=domain) as ssock:
                    cert = ssock.getpeercert()
                    sAN = defaultdict(list)
                    for type_, san in cert['subjectAltName']:
                        sAN[type_].append(san)
                    domain_list_with_san.append(sAN['DNS'])
        except:
            print('Error in SAN for ' + str(domain))


    result = []
    domain_list_tld_extract = []
#    for domain1 in domain_list_with_san:
#        domain_list_tld_extract.append(str(tldextract.extract(str(domain1)).registered_domain))
    # replaces the above
    domain_list_tld_extract = appdom.append_domains_san_to_tld_extract(domain_list_with_san)

    ######
    sanTextSPT = time.time()
    main_logger.warn(f"Time elapsed for textSAN for {shahash} is {sanTextSPT - sanTextST} for {len(domain_list)} domains")
    ######
    #breakpoint()
    if (tldextract.extract(urldomain).registered_domain in domain_list_tld_extract):
        print('Found in domain list')
        stopTime = time.time()
        main_logger.warn(f"Time elapsed for {url} is {stopTime - startTime} with result not phishing")
        result.append({'url': url, 'status': "not phishing", 'sha1': shahash})
        sessions.store_state(uuid, url, 'not phishing', '')
        return jsonify(result)

    sessions.store_state(uuid, url, 'processing', 'imagesearch')

    search = ReverseImageSearch(storage=def_storage, search_engine=list(GoogleReverseImageSearchEngine().identifiers())[0], folder=def_folder, upload=True, mode="image", htmlsession=htmlsession, clf=clf_logo, clearbit=clearbit, tld=tldextract.extract(urldomain).registered_domain)
    search.handle_folder(os.path.join(def_folder, shahash), shahash)
    
    url_list = conn_storage.execute("select distinct result from search_result_image WHERE filepath = ?", (shahash,)).fetchall()

    ######
    sanImgST = time.time()
    ######

    domain_list=[]
    for urls in url_list:
        url_domain = urlparse(urls[0]).netloc
        domain_list.append(url_domain)

    domain_list_with_san = domain_list.copy()

    # Get SAN names and append
    for domain in domain_list:
        try:
            context = ssl.create_default_context()

            with socket.create_connection((domain, 443), timeout=2) as sock:
                with context.wrap_socket(sock, server_hostname=domain) as ssock:
                    cert = ssock.getpeercert()
                    sAN = defaultdict(list)
                    for type_, san in cert['subjectAltName']:
                        sAN[type_].append(san)
                    domain_list_with_san.append(sAN['DNS'])
        except:
            print('Error in SAN for ' + str(domain))


    result = []
    domain_list_tld_extract = []
#    for domain1 in domain_list_with_san:
#        domain_list_tld_extract.append(str(tldextract.extract(str(domain1)).registered_domain))
    # replaces the above
    domain_list_tld_extract = appdom.append_domains_san_to_tld_extract(domain_list_with_san)


    ######
    sanImgSPT = time.time()
    main_logger.warn(f"Time elapsed for imgSAN find for {shahash} is {sanImgSPT - sanImgST}")
    ######

    #breakpoint()
    if (tldextract.extract(urldomain).registered_domain in domain_list_tld_extract):
        print('Found in domain list')
        stopTime = time.time()
        main_logger.warn(f"Time elapsed for {url} is {stopTime - startTime} with result not phishing")
        result.append({'url': url, 'status': "not phishing", 'sha1': shahash})
        sessions.store_state(uuid, url, 'not phishing', '')
        return jsonify(result)
    # no match, go on to image comparison per url

    ######
    compareST = time.time()
    ######

    sessions.store_state(uuid, url, 'processing', 'imagecompare')
    
    out_dir = os.path.join('compare_screens', shahash)
    if not os.path.exists(out_dir):
            os.makedirs(out_dir)
    options = Options()
    options.add_argument( "--headless" )

    url_list = url_list_text + url_list

    # initialize web driver by installing a fresh version of it
    #driver = webdriver.Chrome(ChromeDriverManager().install(), options=options)
    # replaces the above with a fixed ChromeDriver
    driver = webdriver.Chrome('/home/antip/Desktop/codebase/webdriver/94.0.4606.113/chromedriver', options=options)
    driver.set_window_size(image_width, image_height)
    driver.set_page_load_timeout(webdriver_timeout)

    for index, resulturl in enumerate(url_list):
        if (not isinstance(resulturl[0], str)):
            continue
        urllower = resulturl[0].lower()
        if (("www.mijnwoordenboek.nl/puzzelwoordenboek/Dot/1" in resulturl[0]) or ("amsterdamvertical" in resulturl[0]) or ("dotgroningen" in urllower) or ("britannica" in resulturl[0]) or ("en.wikipedia.org/wiki/Language" in resulturl[0]) or (resulturl[0] == '') or (("horizontal" in urllower) and not ("horizontal" in tldextract.extract(resulturl[0]).registered_domain)) or (("vertical" in urllower) and not ("horizontal" in tldextract.extract(resulturl[0]).registered_domain))):
            continue
        # get screenshot of url
        
        try:
            driver.get(resulturl[0])
        except:
            continue
        driver.save_screenshot(out_dir + "/" + str(index) + '.png')

        # image compare
        path_a = "files/" + shahash + "/screen.png"
        path_b = out_dir + "/" + str(index) + ".png"
        emd = None
        dct = None
        s_sim = None
        p_sim = None
        orb = None
        try:
            emd = cl.earth_movers_distance(path_a, path_b)
        except Exception as err:
            main_logger.error(err)
        try:
            dct = cl.dct(path_a, path_b)
        except Exception as err:
            main_logger.error(err)
        try:
            s_sim = cl.structural_sim(path_a, path_b)
        except Exception as err:
            main_logger.error(err)
        try:
            p_sim = cl.pixel_sim(path_a, path_b)
        except Exception as err:
            main_logger.error(err)
        try:
            orb = cl.orb_sim(path_a, path_b)
        except Exception as err:
            main_logger.error(err)
        main_logger.info(f"Compared url '{resulturl[0]}'")
        main_logger.info(f"Finished comparing:  emd = '{emd}', dct = '{dct}', pixel_sim = '{p_sim}', structural_sim = '{s_sim}', orb = '{orb}'")
        
        # return phishing if very similar
        if ((emd < 0.001) and (s_sim > 0.70)) or ((emd < 0.002) and (s_sim > 0.80)):
            driver.quit()
            stopTime = time.time()
            main_logger.warn(f"Time elapsed for {url} is {stopTime - startTime} with result phishing")
            result.append({'url': url, 'status': "phishing", 'sha1': shahash})
            sessions.store_state(uuid, url, 'phishing', '')
            return jsonify(result)
        #otherwise go to next
    
    ######
    compareSPT = time.time()
    main_logger.warn(f"Time elapsed for imgCompare find for {shahash} is {compareSPT - compareST}")
    ######

    driver.quit()

    stopTime = time.time()
    
    # if the inconclusive stems from google blocking:
    #   e.g. blocked == True
    #   result: inconclusive_blocked
    
    main_logger.warn(f"Time elapsed for {url} is {stopTime - startTime} with result inconclusive")
    result.append({'url': url, 'status': "inconclusive", 'sha1': shahash})
    sessions.store_state(uuid, url, 'inconclusive', '')
    return jsonify(result)

@app.route('/api/v1/url/state', methods=['POST'])
def get_url_state():
    json = request.get_json()
    url = json["URL"]
    uuid = json["uuid"]
    currStatus = sessions.get_state(uuid, url)
    result = []
    result.append({'status': currStatus[0], 'state': currStatus[1]})
    return jsonify(result)

# test cases of the user study carried by seminar students
@app.route('/pages/paypal/signin', methods=['GET'])
def get_paypapl_signin():
    return send_file('pages/paypal/signin.html')

@app.route('/pages/paypal/success', methods=['GET'])
def get_paypapl_success():
    return send_file('pages/paypal/success.html')

@app.route('/pages/digid/signin', methods=['GET'])
def get_digid_signin():
    return send_file('pages/digid/signin.html')

@app.route('/pages/digid/signincss', methods=['GET'])
def get_digid_signincss():
    return send_file('pages/digid/digid_css.css')

@app.route('/pages/digid/success', methods=['GET'])
def get_digid_success():
    return send_file('pages/digid/success.html')

@app.route('/pages/immobiliare/signin', methods=['GET'])
def get_immo_signin():
    return send_file('pages/immobiliare/signin.html')

@app.route('/pages/immobiliare/success', methods=['GET'])
def get_immo_success():
    return send_file('pages/immobiliare/success.html')

@app.route('/pages/olx/signin', methods=['GET'])
def get_olx_signin():
    return send_file('pages/olx/signin.html')

@app.route('/pages/olx/success', methods=['GET'])
def get_olx_success():
    return send_file('pages/olx/success.html')

@app.route('/pages/etos/signin', methods=['GET'])
def get_etos_signin():
    return send_file('pages/etos/signin.html')

@app.route('/pages/etos/success', methods=['GET'])
def get_etos_success():
    return send_file('pages/etos/success.html')

@app.route('/pages/mediamarkt/signin', methods=['GET'])
def get_mediamarkt_signin():
    return send_file('pages/mediamarkt/signin.html')

@app.route('/pages/mediamarkt/success', methods=['GET'])
def get_mediamarkt_success():
    return send_file('pages/mediamarkt/success.html')

@app.route('/pages/coutinho/signin', methods=['GET'])
def get_coutinho_signin():
    return send_file('pages/coutinho/signin.html')

@app.route('/pages/coutinho/success', methods=['GET'])
def get_coutinho_success():
    return send_file('pages/coutinho/success.html')

@app.route('/pages/idealista/signin', methods=['GET'])
def get_idealista_signin():
    return send_file('pages/idealista/signin.html')

@app.route('/pages/idealista/success', methods=['GET'])
def get_idealista_success():
    return send_file('pages/idealista/success.html')

# Using this lib to avoid runtimerror with many requests
#__import__('IPython').embed()
nest_asyncio.apply()

# Handle CTRL+C for shutdown
def signal_handler(sig, frame):
    shutdown_server()
signal.signal(signal.SIGINT, signal_handler)

app.run(host="0.0.0.0")

# used for local test with VM
# app.run(host="192.168.56.100")



