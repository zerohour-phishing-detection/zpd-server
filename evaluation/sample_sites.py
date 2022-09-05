# pip install beautifulsoup4
# sample 1000 (fake) phishing and 1000 benign sites
# from pathlib import Path
import sqlite3
from sqlite3 import Error
from os import listdir
from os.path import isfile, join
from random import sample
import requests
import csv
from bs4 import BeautifulSoup

# path = '/run/media/koelio/2TB/VMs/shared/sample/' # old
path = '/run/media/koelio/043C672D7D497290/phishing datasets/benign_sample/sample/'

def select_sites(conn, samples):
    """
    Query URLs by sampled site sha256
    :param conn: the Connection object
    :param samples: list of sha256 values
    :return: urls_pairs - list of working urls
    """
    cur = conn.cursor()
    urls_pairs = [] # list of dictionaries {"url" : , "title" : }
    nof_processed_samples = 0
    nof_skipped_samples = 0

    # sample_formatted = ','.join(["'" + str(elem) + "'" for elem in samples])
    # print("String sample: " + sample_formatted)

    print("3. Retrieve and test URLs" )
    
    # open file reader
    keys = {'url': '', 'title': ''}.keys()
    with open('./' + 'urls.csv', 'w', newline='', encoding='utf-8') as file:
        writer = csv.DictWriter(file, keys)
        writer.writeheader()

        for sample in samples:
            # execute query
            sql_select_url = (f"SELECT url FROM odp_urls WHERE sha256 ='{sample}';")
            
            try:
                cur.execute(sql_select_url)
            except Error as e:
                print("Error selecting URL from DB." + e)
                # print(e)
                print("Current SQL query: " + sql_select_url)

            # get url
            row = cur.fetchone()

            # test url
            try:
                resp = requests.get(url = row[0], timeout=10)
            except requests.Timeout as err:
                # print("Timeout: " + err.message)
                print(row[0] + " timed out. Going on.")
                nof_skipped_samples = nof_skipped_samples + 1
                continue
            except requests.RequestException as err:
                print("Error with requets: ")
                print(err)
                print(row[0] + " got error. Going on.")
                nof_skipped_samples = nof_skipped_samples + 1
                continue

            # add to list
            # if resp.ok:
            if resp.status_code == 200:
                # keep
                # print (row[0] + ' < 400: ' + resp.reason)
                print (row[0] + ' 200: ' + resp.reason)
                # urls.append(row[0])
            else:
                print("Response NOT OK: " + resp.reason)
                nof_skipped_samples = nof_skipped_samples + 1
                continue

            # go to folder/sha256
            curernt_dir = path + sample + "/"
            
            # check if page.html exists
            if not isfile(join(curernt_dir, 'page.html')):
                print("\t" + "No page.html file for: " + sample + ". Going on.")
                nof_skipped_samples = nof_skipped_samples + 1
                continue # skip to next URL

            # get <title> contents
            with open(curernt_dir + "page.html") as obj:
                soup = BeautifulSoup(obj, "html.parser")
                title = soup.find('title') # alternative to below

                # check if title not empty
                if not title:
                    print("\t" + "No <title> found for " + sample + ". Going on.")
                    nof_skipped_samples = nof_skipped_samples + 1
                    continue # skip to next URL

            print("\t" + "Got title: " + str(title))
                
            # make dictionrary {url: title}
            urls_pair = {'url': row[0], 'title': title.string}
            # urls_pair = {'url': row[0], 'title': title.string.strip()}

            # append to list
            urls_pairs.append(urls_pair)

            # write to file
            writer.writerow(urls_pair)

            nof_processed_samples = nof_processed_samples +1
            print("Processed samples so far: " + str(nof_processed_samples))

    print("NOF_processed_samples: " + str(nof_processed_samples))
    print("NOF_skipped_samples: " + str(nof_skipped_samples))

    return urls_pairs

    # UNCOMMENT FOR BULCK PROCESSING (not tested)
    # sql_select_urls = (f"SELECT url FROM odp_urls WHERE sha256 IN ({sample_formatted});")
    # print("SQL query: " + sql_select_urls)
    
    # try:
    #     cur.execute(sql_select_urls)
    # except Error as e:
    #     print("Error selecting URLs from DB: ")
    #     print(e)

    # # rows = cur.fetchall()
    # for x in range(len(cur.fetchall())):
    #     # get url
    #     row = cur.fetchone()
    #     # test URL for response 200
    #     try:
    #         resp = requests.get(url = row[0], timeout=10)
    #     except requests.Timeout as err:
    #         # print("Timeout: " + err.message)
    #         print(row[0] + " timed out. Going on.")
    #         continue
    #     except requests.RequestException as err:
    #         print("Error with requets: " + err.message)

    #     if resp.ok:
    #         # keep
    #         print (row[0] + ' 200 OK!')
    #         urls.append(row[0])

    # return urls
    

def create_connection(db_file):
    """ create a database connection to the SQLite database
        specified by the db_file
    :param db_file: database file
    :return: Connection object or None
    """
    conn = None
    try:
        conn = sqlite3.connect(db_file)
    except Error as e:
        print(e)

    return conn

def main():
    # database = '/run/media/koelio/2TB/VMs/shared/benign-urls.merged.db' # old
    database = '/run/media/koelio/043C672D7D497290/phishing datasets/benign_sample/benign-urls.merged.db'

    # create a database connection
    conn = create_connection(database)

    dirs = listdir(path)

    # print(dirs)
    # sample fake phishing folders
    print("1. Sample URLs from:" + path)
    # test sites
    # sampled_sites = sample(dirs,4)
    # test sites
    # sampled_sites = ['149a1a88898cef5039f0ead23f2762ff95e0ffc77dde6ecf8297b31566d80819','5cf37c854b681e2427a7235ac91dbaa4c0249e365aefe984b32394d104cc48e7']
    sampled_sites = dirs #[0:99]
    print("NOF_samples to process: " + str(len(sampled_sites)))

    # create dictionary/list of urls
    urls = {
    }

    # query sampled URLs with sha256 key from DB
    print("2. Query sampled URLs from DB")
    url_pairs = select_sites(conn, sampled_sites)

    # print("4. Write working URLs to file")
    # keys = url_pairs[0].keys()
    # with open('./' + 'urls.csv', 'w', newline='', encoding='utf-8') as file:
    #     writer = csv.DictWriter(file, keys)
    #     writer.writeheader()
    #     writer.writerows(url_pairs)
        
    print("Finished. Written URLs to " + path + 'urls.csv')
    
if __name__ == '__main__':
    main()