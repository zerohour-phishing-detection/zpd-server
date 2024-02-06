import os
import sys
from urllib.parse import urlparse
import sqlite3
import argparse
import re, string; 

import numpy as np
import matplotlib.pyplot as plt

pattern = re.compile('[\W_]+')

parser = argparse.ArgumentParser()
parser.add_argument('--hit', help='The sqlite file the search results are stored in', required=True)
global args
args = parser.parse_args()
conn_hit   = sqlite3.connect(args.hit)
cursor_hit = conn_hit.cursor();

print("STILL NEED TO UPDATE BROKEN LEAFS")
print("CREATE SYSTEM THAT TAKES FIELD(S) AND SHOWS HOW RESTRICTIONS AFFECT HITRATE + REGIONS FOUND")
	
def getColumnData(columnname, columnname2=None, restriction="", title=None, filename=None):
	if not title:
		title = f"Scatter plot - {columnname}"
	if not filename:
		filename = f"plot-{pattern.sub('', columnname)}"
		
	groupby = ""
	if not columnname2:
		columnname2 = f"count({columnname})"
		groupby = f"group by {columnname}"
		
	if not os.path.exists('plots'):
		os.makedirs('plots')
	
	sql_h = f"select {columnname}, {columnname2} from region_info where filepath in (select distinct filepath from search_result_text where hit <> '' UNION select distinct filepath from search_result_image where hit <> '') {restriction} {groupby}"
	results = cursor_hit.execute(sql_h).fetchall()
	x1 = []
	y1 = []
	for row in results:
		x1.append(row[0])
		y1.append(row[1])
	plt.scatter(x1, y1, marker='^', c='g', alpha=0.6)
	plt.xlabel(columnname)
	plt.ylabel(columnname2)
	plt.title(title,fontsize=20)
	plt.savefig(os.path.join('plots', f"{filename}.hit.png"))
	plt.close()
	
	sql_m = f"select {columnname}, {columnname2} from region_info where filepath not in (select distinct filepath from search_result_text where hit <> '' UNION select distinct filepath from search_result_image where hit <> '') {restriction} {groupby}"
	results = cursor_hit.execute(sql_m).fetchall()
	x2 = []
	y2 = []
	for row in results:
		x2.append(row[0])
		y2.append(row[1])
	plt.scatter(x2, y2, marker='v', c='r', alpha=0.6)
	plt.xlabel(columnname)
	plt.ylabel(columnname2)
	plt.title(title,fontsize=20)
	plt.savefig(os.path.join('plots', f"{filename}.miss.png"))
	plt.close()
	
	plt.scatter(x1, y1, marker='^', c='g', alpha=0.6)
	plt.scatter(x2, y2, marker='v', c='r', alpha=0.6)
	plt.xlabel(columnname)
	plt.ylabel(columnname2)
	plt.title(title,fontsize=20)
	plt.savefig(os.path.join('plots', f"{filename}.png"))
	plt.close()
	
def getColumnData_root(columnname, columnname2=None, fname=None, title=None):
	if not fname:
		fname = f"plot-{pattern.sub('', columnname)}-root"
	if not title:
		title = f"Scatter plot - {columnname} - Root only"
	return getColumnData(columnname, columnname2, "and parent=-1", title, fname)
	
def getColumnData_leaf(columnname, columnname2=None, fname=None, title=None):
	if not fname:
		fname = f"plot-{pattern.sub('', columnname)}-leaf"
	if not title:
		title = f"Scatter plot - {columnname} - Leaf only"
	return getColumnData(columnname, columnname2, "and child=-1", title, fname)
	
getColumnData("xcoord")
getColumnData_root("xcoord")
getColumnData_leaf("xcoord")

getColumnData("ycoord")
getColumnData_root("ycoord")
getColumnData_leaf("ycoord")

getColumnData("xcoord", "ycoord", filename="plot-xy", title="x and y coord")
getColumnData_root("xcoord", "ycoord", "plot-xy-root")
getColumnData_leaf("xcoord", "ycoord", "plot-xy-leaf")

getColumnData("width*height")
getColumnData_root("width*height")
getColumnData_leaf("width*height")

getColumnData("colourcount")
getColumnData_root("colourcount")
getColumnData_leaf("colourcount")

getColumnData("dominant_colour_pct")
getColumnData_root("dominant_colour_pct")
getColumnData_leaf("dominant_colour_pct")

getColumnData("colourcount", "dominant_colour_pct", filename="plot-colour-and-percent", title="Colour count and percentage")
getColumnData_root("colourcount", "dominant_colour_pct", "plot-colour-and-percent-root")
getColumnData_leaf("colourcount", "dominant_colour_pct", "plot-colour-and-percent-leaf")