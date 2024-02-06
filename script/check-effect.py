import os
import sys
from urllib.parse import urlparse
import sqlite3
import argparse
import pandas as pd

conn_p   = sqlite3.connect("storage.phishing.db")
conn_b   = sqlite3.connect("storage.benign.db")

def gettotal(conn):
	'''
		Gets total number of websites in the sqlite DB
	'''
	inter = 0
	results = conn.execute("select distinct filepath from search_result_image union select distinct filepath from search_result_text").fetchall()
	for row in results:
		inter += 1
	return inter

def getdata(name, restriction_str, conn, total):
	'''
		Gets data from the sqlite DB's and returns the accuracy in %, the mean regions found and the std of regions found
	'''
	sql_acc = f"select distinct search_result_image.filepath from search_result_image, region_info where hit <> '' and search_result_image.filepath = region_info.filepath and search_result_image.region = region_info.region {restriction_str} UNION select distinct filepath from search_result_text where hit <> ''"
	sql_q = f"select region_info.filepath, count(xcoord) as cnt from region_info where {restriction_str[4:]} group by region_info.filepath UNION SELECT region_info.filepath, 0 as cnt from region_info where filepath not in (select distinct region_info.filepath from region_info where {restriction_str[4:]})"
	
	print(sql_q)
	df = pd.read_sql_query(sql_q, conn)
	hits = set()
	results = conn.execute(sql_acc).fetchall()
	for row in results:
		hits.add(row[0])
	pct = len(hits)/total*100
	print(f"{name}: {pct:.2f}% {df['cnt'].mean():.2f} {df['cnt'].std():.2f}")
	
def effect(restriction):
	'''
		Formats input array to a SQL restriction on regions found and prints performance of the filter
	'''

	restriction_str = ""
	for restr in restriction:
		restriction_str += f" AND {restr}"	
		
	getdata("Phishing", restriction_str, conn_p, total_p)
	getdata("Benign", restriction_str, conn_b, total_b)

# Storing total intermediately incase we want to try multiple filters in one run
total_p = gettotal(conn_p)
total_b = gettotal(conn_b)

effect(
	[
		"region_info.dominant_colour_pct > 4", "region_info.dominant_colour_pct < 82", "region_info.colourcount > 30", "region_info.colourcount < 8572", "region_info.width*region_info.height < 9262", "region_info.width*region_info.height > 782", "region_info.xcoord > 50", "region_info.xcoord < 1000", "region_info.ycoord > 10", "region_info.ycoord < 750"
	]
)
effect(
	[
		"1=1"
	]
)