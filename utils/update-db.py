import cv2
import numpy as np
import sqlite3

def count_colours(src):
	unique, counts = np.unique(src.reshape(-1, src.shape[-1]), axis=0, return_counts=True)
	return (len(unique), np.amax(counts, initial=0)/np.sum(counts)*100)

def get_image_data(hash):
    image = cv2.imread(imgpath, 1)
    imgdata = [count_colours(image), image.shape[0], image.shape[1]]

conn_storage = sqlite3.connect("storage.dem.tree.db")

sql_q_db = '''
    CREATE TABLE IF NOT EXISTS "screen_info" (
                "filepath"	string,
                "width"	integer,
                "height" integer,
                "colourcount" integer,
                "dominant_colour_pct" integer
            );'''
conn_storage.execute(sql_q_db)
conn_storage.commit()

handled_resp = self.conn_storage.execute("select distinct filepath from region_info").fetchall()
for fp in handled_resp:
    shahash = fp[0]
    imgdata = get_image_data(shahash)
    conn_storage.execute("INSERT INTO screen_info (filepath, width, height, colourcount, dominant_colour_pct) VALUES (?, ?, ?, ?, ?)", (shahash, imgdata[2], imgdata[1], imgdata[0][0], imgdata[0][1]))
    conn_storage.commit()
