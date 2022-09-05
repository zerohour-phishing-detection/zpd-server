import os
import sqlite3

# Mode: benign or phishing
mode = "phishing"

# The last hash that you have labeled, so not the first one you have not
last_hash = "1afd62716b8b4b857ae9eacf3b204e2a7a780aa4"

def_folder = f"{mode}-rawdata/{mode}/files"
def_storage = f"db/new_region_data_{mode}_labeled_filtered.db" 
new_folder = f"{mode}-rawdata/{mode}/sample"

conn_storage = sqlite3.connect(def_storage)

list_name = os.listdir(new_folder)

def label():
    found = False
    count = 0
    for i in range(len(list_name)):
        if list_name[i] == last_hash:
            found = True
            print(f"Hash index found")
        elif found:
            conn_storage.execute(f"delete from region_info where filepath = '{list_name[i]}'")
            conn_storage.commit()
    labeled_count = conn_storage.execute(f"select count(distinct filepath) from region_info").fetchone()[0]
    logo_count = conn_storage.execute(f"select count(*) from region_info where label = 'logo'").fetchone()[0]
    nonlogo_count = conn_storage.execute(f"select count(*) from region_info where label <> 'logo'").fetchone()[0]
    print(f"Total screenshots labeled: {str(labeled_count)}")
    print(f"Total logo regions: {str(logo_count)}")
    print(f"Total non logo regions: {str(nonlogo_count)}")
    
label()