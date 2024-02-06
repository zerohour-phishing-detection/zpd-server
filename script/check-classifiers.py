from requests_html import HTMLSession
import asyncio
import utils.utils as ut
import utils.classifiers as cl
from utils.customlogger import CustomLogger
import hashlib
import os
import argparse
import sqlite3
import time
import signal

main_logger = CustomLogger().main_logger

parser = argparse.ArgumentParser()
parser.add_argument('--hit', help='The sqlite file the search results are stored in', required=True)
parser.add_argument('--type', help='phishing or benign', required=True)
parser.add_argument('--skip', type=int, default=0,  help='Starting skip')
global args
args = parser.parse_args()
conn_hit   = sqlite3.connect(args.hit)

root_path = "/media/root/Samsung_T5/phishing-db/"
if not os.path.exists(root_path):
    def_base_vm = "/media/sf_Samsung_T5/phishing-db/"
    if os.path.exists(def_base_vm):
        main_logger.info("VM folders detected. setting default variables to VM.")
        root_path = def_base_vm
    else:
        root_path = ""

if args.type == 'api':
	orig_dir = f"{root_path}files"
else:
	orig_dir = f"{root_path}{args.type}-rawdata/{args.type}/files"
output_dir = f"{root_path}verify/files"

async def _handle_page(html, path):
	await html.page.setViewport({'width': 1280, 'height': 768})
	await html.page.screenshot({'path': os.path.join(path, "screen.png")})
	
	html_str = await html.page.content()
	with open(os.path.join(path, "page.html"), "w") as text_file:
		text_file.write(html_str)
	
	img_size = 0
	html_size = 0
	if os.path.exists(os.path.join(path, "screen.png")):
		img_size = os.path.getsize(os.path.join(path, "screen.png"))
	if os.path.exists(os.path.join(path, "page.html")):
		html_size = os.path.getsize(os.path.join(path, "page.html"))
		
	main_logger.info(f"Image size: {img_size} bytes")
	main_logger.info(f"HTML size: {html_size} bytes")
	
	await html.page.close()

def alarmhandler(signum, frame):
	main_logger.error(f"Response took longer then allowed. Cancelling")
	raise IOError("Did not receive response.")
		
def cap_screen(url, session):
	signal.signal(signal.SIGALRM, alarmhandler)
	signal.alarm(240)
	hash_val = hashlib.sha1(url.encode()).hexdigest()
	curr_dir = os.path.join(output_dir, hash_val)
	if not os.path.exists(curr_dir):
		os.makedirs(curr_dir)
	main_logger.info(f"Downloading: [{hash_val}] {url}")
	req = session.post(url)
	req.html.render(sleep=1, timeout=4.0, keep_page=True)
	asyncio.get_event_loop().run_until_complete(_handle_page(req.html, curr_dir))
	signal.alarm(0)
	return hash_val
	
def get_screen(url):
	session = HTMLSession()
	v = cap_screen(url, session)
	session.close()
	os.system("pkill chrome")
	return v


#query = f"select distinct result, hit from search_result_image union select distinct result, hit from search_result_text order by hit desc"
# Columns not in the initial DB:
columns = {'resulthash' : 'string', 'emd' : 'float', 'dct': 'float', 'pixel_sim': 'float', 'structural_sim': 'float', 'orb': 'float'}
try:
	for col in columns:
		sql_q_db = '''
		ALTER TABLE search_result_image
		ADD COLUMN "{}" {}'''
		conn_hit.execute(sql_q_db.format(col, columns[col]));
			
		sql_q_db = '''
		ALTER TABLE search_result_text
		ADD COLUMN "{}" {}'''
		conn_hit.execute(sql_q_db.format(col, columns[col]));
		
	conn_hit.commit();
except sqlite3.Error as er:
	print("Did not update database schema, might already be up to date. (" + str(er) + ")")

# Query to compare all origins to the image results
#query = "select distinct filepath, result, orb from search_result_image union select distinct filepath, result, orb from search_result_text order by orb asc"
query = "select distinct filepath, result, orb from search_result_image where region = 9999 order by orb asc"
url_list = conn_hit.execute(query).fetchall()

# Dirty hack for logging to get all results. due to row cnt being shitty with sqlite interface
total = 0
for row in url_list:
	total += 1

curr = 0
skipped = 0
url_list = conn_hit.execute(query).fetchall()
start = time.time()
for row in url_list:
	curr += 1
	
	os.system("pkill chrome")
	
	if curr < args.skip:
		print(f"Skipping: {curr}/{args.skip}", end="\r")
		continue
		
	# Somehow cancel alarm can linger despite us cancelling it before
	signal.alarm(0)
	ut.setstatus(f"{curr}/{total} ({curr/total*100:.2f}%) - Skipped: {skipped} ({skipped/total*100:.2f}%) - {ut.timeString(start, curr, total)}")
	
	db_hash = row[0]
	url = row[1]
	hash_val = hashlib.sha1(url.encode()).hexdigest()
	
	# Path to a screen found by search engine
	path_a = os.path.join(output_dir, hash_val, "screen.png")
	
	# Path to a screen of the suspicious website
	path_b = os.path.join(orig_dir, db_hash, "screen.png")
	
	if not os.path.exists(path_a):
		try:
			get_screen(url)
			main_logger.info(f"Downloaded: {url}")
		except Exception as err:
			main_logger.error(err)
			signal.alarm(0)
			skipped += 1
			continue
	
	# Image comparisons
	main_logger.info(f"[{curr}/{total} | {skipped}] Performing image comparisons on:")
	main_logger.info(f"[{curr}/{total} | {skipped}] {row[0]}")
	main_logger.info(f"[{curr}/{total} | {skipped}] {hash_val} - {url}")
	
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
	
	main_logger.info(f"[{curr}/{total} | {skipped}] Finished comparing storing results:  emd = '{emd}', dct = '{dct}', pixel_sim = '{p_sim}', structural_sim = '{s_sim}', orb = '{orb}'")
	
	q_1 = f"update search_result_image set resulthash = ?, emd = ?, dct = ?, pixel_sim = ?, structural_sim = ?, orb = ?  where filepath = ? and result = ?"
	conn_hit.execute(q_1, (hash_val, emd, dct, p_sim, s_sim, orb, row[0], url))
	
	q_2 = f"update search_result_text set resulthash = ?, emd = ?, dct = ?, pixel_sim = ?, structural_sim = ?, orb = ?  where filepath = ? and result = ?"
	conn_hit.execute(q_2, (hash_val, emd, dct, p_sim, s_sim, orb, row[0], url))
	
	main_logger.info(f"[{curr}/{total} | {skipped}] Updated database entry")
	
	conn_hit.commit()
	