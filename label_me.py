import os
import shutil
import sqlite3
import webbrowser
import pathlib
from selenium import webdriver
from utils.reverseimagesearch import ReverseImageSearch
from engines.google import GoogleReverseImageSearchEngine
from requests_html import HTMLSession

# Mode: benign or phishing
mode = "phishing"

htmlsession = HTMLSession()
htmlsession.browser

def_folder = f"{mode}-rawdata/{mode}/files"
def_storage = f"db/new_region_data_{mode}_labeled.db" 
new_folder = f"{mode}-rawdata/{mode}/sample"

conn_storage = sqlite3.connect(def_storage)

list_name = os.listdir(new_folder)

browser = webdriver.Firefox()

def label():
    count = 0
    for i in range(len(list_name)):
        logo_count = conn_storage.execute(f"select count(*) from region_info where filepath = '{list_name[i]}' and label = 'logo'").fetchone()[0]
        region_count = conn_storage.execute(f"select count(*) from region_info where filepath = '{list_name[i]}'").fetchone()[0]
        if logo_count > 0 or region_count == 0:
            continue
        browser.get("file://" +  os.path.join(pathlib.Path(__file__).parent.resolve(), new_folder, list_name[i], "Highlight.png"))
        valid_command = False
        while not valid_command:
            command = input("Please enter (a list of) region id of logo or type del to delete entry from database: ")
            if command.strip() == "del":
                # e.g., for invalid screenshot, remove from database and delete files
                conn_storage.execute(f"delete from region_info where filepath = '{list_name[i]}'")
                conn_storage.commit()
                shutil.rmtree(os.path.join(new_folder, list_name[i]))
                valid_command = True
            if command.strip() == "none":
                count = count + 1
                valid_command = True
            if command.strip() == "shuffle":
                print("shuffling")
                conn_storage.execute(f"delete from region_info where filepath = '{list_name[i]}'")
                conn_storage.commit()
                search = ReverseImageSearch(storage=def_storage, search_engine=list(GoogleReverseImageSearchEngine().identifiers())[0], folder=def_folder, upload=False, mode="image", htmlsession=htmlsession)
                search.handle_folder(os.path.join(new_folder, list_name[i]), list_name[i])
                browser.get("file://" +  os.path.join(pathlib.Path(__file__).parent.resolve(), new_folder, list_name[i], "Highlight.png"))
            if command.strip().strip("-").isnumeric():
                # label this region id as logo
                if int(command.strip()) < 0:
                    conn_storage.execute(f"update region_info set label = 'logo' where region = {command.strip().strip('-')} and filepath = '{list_name[i]}' and invert = '1'")
                else:
                    conn_storage.execute(f"update region_info set label = 'logo' where region = {command.strip()} and filepath = '{list_name[i]}' and invert = '0'")
                conn_storage.commit()
                count = count + 1
                valid_command = True
            if "," in command:
                number_list = command.split(",")
                try:
                    numbers = [int(x.strip()) for x in number_list]
                except:
                    print('List contained non-numbers, please try again (e.g. "1, 42, 69"')
                if len(numbers) > 0:
                    valid_command = True
                    for id in numbers:
                        # UPDATE statement
                        if id < 0:
                            conn_storage.execute(f"update region_info set label = 'logo' where region = {id*-1} and filepath = '{list_name[i]}' and invert = '1'")
                        else:
                            conn_storage.execute(f"update region_info set label = 'logo' where region = {id} and filepath = '{list_name[i]}' and invert = '0'")
                    count = count + 1
                    conn_storage.commit()
            if command.strip() == "stop":
                print(f"labeled {str(count)} items")
                browser.close()
                return
            if ((not valid_command) and (command.strip() != "shuffle")):
                print("Invalid. (valid: (list of) numbers, del, none, stop, shuffle)")
    
label()