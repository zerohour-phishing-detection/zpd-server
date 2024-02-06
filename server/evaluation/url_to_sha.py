import hashlib
import csv
import sqlite3
from sqlite3 import Error as SQLError
import requests

def create_connection(db_file):
    """ create a database connection to the SQLite database
        specified by the db_file
    :param db_file: database file
    :return: Connection object or None
    """
    conn = None
    try:
        conn = sqlite3.connect(db_file)
    except SQLError as e:
        print("Error creating connection to DB")
        print(e.__str__())

    return conn

def add_hashes(conn,urls,test=True):
    """
    Query write hashes of urls
    :param conn: the Connection object
    :return:
    """

    sql_create_urls_table = '''CREATE TABLE IF NOT EXISTS odp_urls (                                        
                                        url text PRIMARY KEY,
                                        title text,
                                        sha256 text
                                   );'''

    # create tables
    try:
        c = conn.cursor()
        c.execute(sql_create_urls_table)
        print("Successfully created odp_urls table or already exists")
    except SQLError as e:
        print("Error creating odp_urls table")
        print(e.__str__())

    if test:
        try:
            conn.execute("DELETE FROM odp_urls")
            conn.commit()
            print("Successfully deleted from odp_urls table")
        except SQLError as e:
            print("Error emptying odp_urls table")
            print(e.__str__())

    # set counter
    i = 0
    for url in urls:
    # for url in urls[i:len(urls)]:
        if not url[1].strip():
            print("Stripped title of " + url[0] + " is empty. Going on.")
            # i = i + 1
            continue
        else:
            url[1] = url[1].strip()
            #strip from quotes
            url[1] = url[1].strip('\"')

        sql = ''' INSERT INTO odp_urls(url,title,sha256)
                VALUES(?,?,?) '''

        try:
            print("Requesting orig url: " + url[0])
            resp = requests.get(url[0], timeout = 120, allow_redirects = True)
            last_url = resp.url
            print("Last resp url:" + last_url)
            # shahash = hashlib.sha1(last_url.encode('utf-8')).hexdigest()
            shahash = hashlib.sha256(last_url.encode('utf-8')).hexdigest()
            # for r in resp.history:
            #     print("Resp url: " + str(r.status_code) + " " + r.url)
                # shahash = hashlib.sha256(resp.url.encode('utf-8')).hexdigest()
            # else:
            #     print("Response NOT OK: " + resp.reason + " Writing old url.")
            #     shahash = hashlib.sha1(url[0].encode('utf-8')).hexdigest()
                # shahash = hashlib.sha256(url[0].encode('utf-8')).hexdigest()
                # continue
        except requests.Timeout as err:
            print(str(url[0]) + " timed out. Going on. Writing old url.")
            print(err)
            shahash = hashlib.sha1(url[0].encode('utf-8')).hexdigest()
            # continue
        except requests.RequestException as err:
            print("Error with requets: ")
            print(err)
            print(url[0] + " got error. Going on. Writing old url.")
            shahash = hashlib.sha1(url[0].encode('utf-8')).hexdigest()
            # continue


       	# shahash = hashlib.sha1(url[0].encode('utf-8')).hexdigest()
       	# shahash = hashlib.sha256(url[0].encode('utf-8')).hexdigest()

        row = (last_url,url[1],shahash)

        try:
            cur = conn.cursor()
            cur.execute(sql, row)
            conn.commit()
            print(str(i) + "th url inserted")
            i = i + 1
        except SQLError as e:
            print("Error inserting record into odp_urls table")
            print(e.__str__())

    print("Inserting records into 'odp_urls' table completed.")
    return i

def read_urls(path=None):

    if not path:
        # list of test URLs [URL,title]
        urls = [
        ['https://versicherung.ge-be-in.de/startseite', "Sterbegeldversicherung seit 1923 - GE·BE·IN Versicherungen"], 
        ['https://idsrv.lv1871.de/Login', '"Lebensversicherung von 1871 a. G. München"'],
        ['http://www.rogerebert.com/reviews/reservoir-dogs-1992', 'Reservoir Dogs movie review &amp; film summary (1992) | Roger Ebert'],
        ['http://www.kuselit.de/', ':: Kuselit Verlag :: Rechtsbibliografie'],
        ['http://www.ullapoolholidayhomes.com/', 'Holiday Accommodation Self Catering Cottages | Ullapool Scotland NC500'],
        ['http://www.art-und-tat.de/', 'Veronika Jakob Grafikdesign'],
        ['http://www.tuffies.co.uk/', 'Buy Luxury Dog Beds UK Online | British Handmade Heavy Duty &amp; Chew Proof Dog Beds | Tuffies'],
        # ['http://www.comune.pietraperzia.en.it/', 'Comune di Pietraperzia'],
        ['http://www.traditieialomita.ro/', 'Tradiție și Modernism – Centrul Județean pentru Conservarea și Promovarea Culturii Tradiționale Ialomița'],
        ['http://www.theglenlyngorge.co.uk/', '\n']
        #['http://www.kronos.co.uk/', 'Workforce Management and HCM Cloud Solutions | Kronos UK']
        ]

        return urls

    urls = []

    with open(path, newline='') as csvfile:
        reader = csv.reader(csvfile, delimiter=',') # encoding='utf-8'
        next(reader) # skip header    
        for row in reader:
            # print("Reading: " + ', '.join(row))
            url_pair = [row[0],row[1]]
            urls.append(url_pair)

    return urls

def main():
    # path_db = "data/benign_urls.db"
    path_db = "data/phishing_urls.db"
    # path_urls = "data/benign_urls.csv"
    path_urls = "data/fake_urls.csv"
    conn = create_connection(path_db)

# get all available urls
    print("Reading from " + path_urls)
    urls = read_urls(path_urls)

    # add hashes
    tot_inserted = add_hashes(conn,urls,True)
    print(str(tot_inserted) + " urls inserted.")

if __name__ == '__main__':
    main()