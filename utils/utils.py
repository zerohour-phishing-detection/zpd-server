'''
    Just some misc util funcs that might be universally used
'''

import time
import requests
import sys
import os
import stat
from bs4 import BeautifulSoup
from datetime import datetime
import sqlite3

# Setup logging
from utils.custom_logger import CustomLogger
main_logger = CustomLogger().main_logger

def toFile(filename: str, string: str):
    with open(filename, "w") as f:
        f.write(string)

def store_handles(hash, regid):
    toFile(f"response/{hash} - {regid} - {time.time()}.log", fd_table_status_str())

def timeFormat(inp):
    m, s = divmod(inp, 60)
    h, m = divmod(m, 60)
    return f'{h:2.0f}h {m:2.0f}m {s:5.2f}s'

def get_search_term(path, hash):
    html_file = os.path.join(path, hash, 'page.html')
    if not os.path.isfile(html_file):
        return ""
    with open(html_file, 'r') as f:
        soup = BeautifulSoup(f, "html.parser")
        if soup.title:
            if soup.title.string:
                return soup.title.string.strip()
            else:
                return soup.title.string
        else:
            return ""

def timeString(timeStart, i, N):
    now = time.time();
    elapsed = now - timeStart;
    totalTimeExpected = max((elapsed/i)*(N-1), elapsed);
    remainingTime = max(totalTimeExpected-elapsed, 0);
    return f"Elapsed: {timeFormat(elapsed)} - Remaining: {timeFormat(remainingTime)} - Expected: {timeFormat(totalTimeExpected)}"

def get_ip():
    response = requests.post("http://ident.me")
    return response.text

startupip=get_ip()
def setstatus(status):
    toFile(f"log/status-{startupip}.txt", status)


def fix_entries(search, def_db):
    '''
    main_logger.info("Adding entries not in new DB")
    search.conn_storage.execute(f"ATTACH '{def_db}' as dba")
    sql = "select sha1 from dba.urls where sha1 not in (select sha1 from brand_table)"
    results = search.conn_storage.execute(sql).fetchall()
    issue = set()
    start1 = time.time()
    for row in results:
        issue.add(row[0])
    main_logger.error(f"{len(issue)} missing entries found.")
    cnt = 0
    for row in issue:
        cnt += 1
        setstatus(f"{cnt}/{len(issue)} ({cnt/len(issue)*100}%) - {timeString(start1, cnt, len(issue))}")
        search.handle_folder(os.path.join(search.folder, row), row)
    search.conn_storage.execute("detach database dba")
    '''

    main_logger.info("Double checking where no title results exist")
    search.mode = "text"
    sql = "select distinct sha1 from brand_table where sha1 not in (select distinct filepath from search_result_text)"
    results = search.conn_storage.execute(sql).fetchall()
    issue2 = set()
    start2 = time.time()
    for row in results:
        issue2.add(row[0])
    main_logger.error(f"Stage Text: {len(issue2)} missing entries found.")
    cnt = 0
    for row in issue2:
        cnt += 1
        setstatus(f"Stage Title: {cnt}/{len(issue2)} ({cnt/len(issue2)*100}%) - {timeString(start2, cnt, len(issue2))}")
        search.handle_folder(os.path.join(search.folder, row), row)

    main_logger.info("Double checking where no image results exist")
    search.mode = "image"
    sql = "select distinct sha1 from brand_table where sha1 not in (select distinct filepath from search_result_image)"
    results = search.conn_storage.execute(sql).fetchall()
    issue3 = set()
    start3 = time.time()
    for row in results:
        issue3.add(row[0])
    main_logger.error(f"{len(issue3)} missing image found.")
    cnt = 0
    for row in issue3:
        cnt += 1
        setstatus(f"Stage Image: {cnt}/{len(issue3)} ({cnt/len(issue3)*100}%) - {timeString(start3, cnt, len(issue3))}")
        search.handle_folder(os.path.join(search.folder, row), row)
