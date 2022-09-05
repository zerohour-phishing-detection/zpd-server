import pandas as pd
import numpy as np
import os
import shutil
import sqlite3
import webbrowser
import pathlib
from selenium import webdriver
from utils.reverseimagesearch import ReverseImageSearch
from engines.google import GoogleReverseImageSearchEngine
from requests_html import HTMLSession

def_storage_phish = "db/storage.phishing-copy.db"
def_storage_benign = "db/storage.benign-copy.db"
phish_data_folder = 'phishing-rawdata/phishing/files'
benign_data_folder = 'benign-rawdata/benign/files'
new_db_phish = 'db/storage.phishing-new.db'
new_db_benign = 'db/storage.benign-new.db'

htmlsession = HTMLSession()
htmlsession.browser

# get phishing region data in dataframe
conn = sqlite3.connect(def_storage_phish)
df_phish = pd.read_sql_query("SELECT * from region_info", conn)
conn.close()

# get benign region data in dataframe
conn = sqlite3.connect(def_storage_benign)
df_benign = pd.read_sql_query("SELECT * from region_info", conn)
conn.close()

phish_filepaths = df_phish['filepath'].unique()
benign_filepaths = df_benign['filepath'].unique()

search = ReverseImageSearch(storage=new_db_benign, search_engine=list(GoogleReverseImageSearchEngine().identifiers())[0], folder=benign_data_folder, upload=False, mode="image", htmlsession=htmlsession)

for filepath in benign_filepaths:
    if os.path.isdir(os.path.join(benign_data_folder, filepath)):
        search.handle_folder(os.path.join(benign_data_folder, filepath), filepath)

conn = sqlite3.connect(new_db_benign)
df_new_benign= pd.read_sql_query("SELECT * from region_info", conn)
conn.close()
print(df_new_benign.head())