import os
import sys
from urllib.parse import urlparse
import sqlite3
import argparse
import tldextract
import socket
import ssl
from collections import defaultdict
from itertools import chain

parser = argparse.ArgumentParser()
parser.add_argument('--hit', help='The sqlite file the search results are stored in', required=True)
parser.add_argument('--url', help='The sqlite file the original urls were stored in', required=True)
global args
args = parser.parse_args()

conn_url	  = sqlite3.connect(args.url)
conn_hit   = sqlite3.connect(args.hit)

whitelist = {
		'amazon' : ("amazon.com", "amazon.fr", "amazon.it", "amazon.de", "amazon.ca",
		"amazon.co.uk", "amazon.in", "amazon.ru", "amazon.nl", "amazon.com.mx",
		"amazon.es", "amazon.com.au", "amazon.com.br", "ssl-images-amazon.com",
		"amazon-adsystem.com", "assoc-amazon.com", "payments-amazon.com",
		"media-amazon.com", "amazon.co.jp", "amazon.eu", "amazon-corp.com",
		"amazon.cn", "amazon.jobs"),

		'apple' : ("apple.com", "icloud.com", "mac.com", "airport.com", "applecomputer.com",
		"appleimac.com", "imac.com", "iphone.com", "iphone.org", "ipod.com",
		"itunes.com", "applemusic.com"),

		'AT&T' : ("att.com"),

		'alibaba' : ("alibaba.com"),

		'allegro' : ("allegro.pl"),

		'bankofamerica' : ("www.bankofamerica.com", 'bankofamerica.com'),

		'chase' : ("chase.com", "www.chase.com"),

		'citibanl' : ("citi.com", "citibank.com"),

		'coinbase' : ("coinbase.com"),

		'cox' : ("cox.com", "cox.net", "coxbusiness.com"),

		'docusign' : ("docusign.com", "docusign.net", "docusign.de", "docusign.fr",
		"docusign.nl", "docusign.be", "docusign.se", "docusign.no",
		"docusign.fi", "docusign.pt", "docusign.lt", "docusign.in"),

		'dropbox' : ("db.tt", "dropbox.com", "dropboxapi.com", "dropboxbusiness.com",
		"dropboxdocs.com", "dropboxforums.com", "dropboxforum.com",
		"dropboxinsiders.com", "dropboxmail.com", "dropboxpartners.com",
		"dropboxstatic.com", "dropbox.zendesk.com", "getdropbox.com"),

		'facebook' : ("facebook.com", "fbcdn.net", "fb.me", "fbsbx.com"),

		'google' : ("google.com", "google.ad", "google.ae", "google.com.af",
		"google.com.ag", "google.com.ai", "google.al", "google.am",
		"google.co.ao", "google.com.ar", "google.as", "google.at",
		"google.com.au", "google.az", "google.ba", "google.com.bd", "google.be",
		"google.bf", "google.bg", "google.com.bh", "google.bi", "google.bj",
		"google.com.bn", "google.com.bo", "google.com.br", "google.bs",
		"google.bt", "google.co.bw", "google.by", "google.com.bz", "google.ca",
		"google.cd", "google.cf", "google.cg", "google.ch", "google.ci",
		"google.co.ck", "google.cl", "google.cm", "google.cn", "google.com.co",
		"google.co.cr", "google.com.cu", "google.cv", "google.com.cy",
		"google.cz", "google.de", "google.dj", "google.dk", "google.dm",
		"google.com.do", "google.dz", "google.com.ec", "google.ee",
		"google.com.eg", "google.es", "google.com.et", "google.fi",
		"google.com.fj", "google.fm", "google.fr", "google.ga", "google.ge",
		"google.gg", "google.com.gh", "google.com.gi", "google.gl", "google.gm",
		"google.gp", "google.gr", "google.com.gt", "google.gy", "google.com.hk",
		"google.hn", "google.hr", "google.ht", "google.hu", "google.co.id",
		"google.ie", "google.co.il", "google.im", "google.co.in", "google.iq",
		"google.is", "google.it", "google.je", "google.com.jm", "google.jo",
		"google.co.jp", "google.co.ke", "google.com.kh", "google.ki",
		"google.kg", "google.co.kr", "google.com.kw", "google.kz", "google.la",
		"google.com.lb", "google.li", "google.lk", "google.co.ls", "google.lt",
		"google.lu", "google.lv", "google.com.ly", "google.co.ma", "google.md",
		"google.me", "google.mg", "google.mk", "google.ml", "google.com.mm",
		"google.mn", "google.ms", "google.com.mt", "google.mu", "google.mv",
		"google.mw", "google.com.mx", "google.com.my", "google.co.mz",
		"google.com.na", "google.com.nf", "google.com.ng", "google.com.ni",
		"google.ne", "google.nl", "google.no", "google.com.np", "google.nr",
		"google.nu", "google.co.nz", "google.com.om", "google.com.pa",
		"google.com.pe", "google.com.pg", "google.com.ph", "google.com.pk",
		"google.pl", "google.pn", "google.com.pr", "google.ps", "google.pt",
		"google.com.py", "google.com.qa", "google.ro", "google.ru", "google.rw",
		"google.com.sa", "google.com.sb", "google.sc", "google.se",
		"google.com.sg", "google.sh", "google.si", "google.sk", "google.com.sl",
		"google.sn", "google.so", "google.sm", "google.sr", "google.st",
		"google.com.sv", "google.td", "google.tg", "google.co.th",
		"google.com.tj", "google.tk", "google.tl", "google.tm", "google.tn",
		"google.to", "google.com.tr", "google.tt", "google.com.tw",
		"google.co.tz", "google.com.ua", "google.co.ug", "google.co.uk",
		"google.com.uy", "google.co.uz", "google.com.vc", "google.co.ve",
		"google.vg", "google.co.vi", "google.com.vn", "google.vu", "google.ws",
		"google.rs", "google.co.za", "google.co.zm", "google.co.zw",
		"google.cat", "google.com.pt", "google.kr", "google.com.dz",
		"google.sl", "google.do", "google.sg", "google.com.bi", "google.tw",
		"google.mx", "google.com.lv", "google.vn", "google.qa", "google.ph",
		"google.pk", "google.jp", "google.com.gr", "google.com.cn", "google.ng",
		"google.hk", "google.ua", "google.co.hu", "google.it.ao",
		"google.com.pl", "google.com.ru", "google.ne.jp", "google.com.cn",
		"chrome.com", "android.com", "google-analytics.com", "gmail.com",
		"blog.google", "domains.google", "google.org", "ai.google", "withgoogle.com"),

		'instagram' : ("instagram.com"),

		'linkedin' : ("linkedin.com", "linked.in"),

		'localbitcoins' : ("localbitcoins.com"),

		'magalu' : ("magazineluiza.com.br"),

		'microsoft' : ("microsoft.com", "microsoftonline.com", "office.com", "live.com",
		"onedrive.com", "s-microsoft.com", "sharepoint.com", "microsoft.us",
		"msft.net", "microsoft-int.com", "outlook.com"),

		'netflix' : ("netflix.adult", "netflix.af", "netflix.ag", "netflix.ai",
		"netflix.asia", "netflix.at", "netflix-australia.com", "netflix.ax",
		"netflix.berlin", "netflix.bg", "netflix.bi", "netflix.buzz",
		"netflix.bz", "netflix.cat", "netflix.cc", "netflix.ceo", "netflix.cf",
		"netflix.club", "netflix.cm", "netflix.cn", "netflix.co",
		"netflix.co.ag", "netflix.co.at", "netflix.co.bi", "netflix.co.bw",
		"netflix.co.cm", "netflix.co.gl", "netflix.co.gy", "netflix.co.in",
		"netflix.co.ke", "netflix.co.kr", "netflix.co.lc", "netflix.com",
		"netflix.com.af", "netflix.com.ag", "netflix.com.ai", "netflix.com.bi",
		"netflix.com.bz", "netflix.com.cm", "netflix.com.cn", "netflix.com.co",
		"netflix.com.de", "netflix.com.ec", "netflix.com.gl", "netflix.com.gp",
		"netflix.com.gt", "netflix.com.gy", "netflix.com.hk", "netflix.com.hn",
		"netflix.com.ht", "netflix-com.ie", "netflix.com.lc", "netflix.com.lv",
		"netflix.com.ly", "netflix.com.mg", "netflix.com.ms", "netflix.com.mw",
		"netflix.com.ng", "netflix.com.pa", "netflix.com.pe", "netflix.com.pr",
		"netflix.com.ps", "netflix.com.sb", "netflix.com.sc", "netflix.com.sg",
		"netflix.com.sl", "netflix.com.sn", "netflix.com.tj", "netflix.com.tw",
		"netflix.com.ua", "netflix-com.uk", "netflix.com.vc", "netflix.com.vi",
		"netflix.co.mw", "netflix.co.nz", "netflix.co.pn", "netflix.co.tj",
		"netflix.co.tz", "netflix.co.ug", "netflix.co.vi", "netflix.co.za",
		"netflix-customerservice.com", "netflix.cx", "netflix.cz", "netflix.de",
		"netflix.ec", "netflix.film", "netflix.firm.in", "netflix.fm",
		"netflix-forever.de", "netflix.fr", "netflix.ga", "netflix.gd",
		"netflix.gen.in", "netflix.gl", "netflix.gp", "netflix.gq",
		"netflix.gs", "netflix.gy", "netflix.hk", "netflix.hn", "netflix.horse",
		"netflix.ht", "netflix.id", "netflix.in", "netflix-inc.com",
		"netflix.ind.in", "netflix.info", "netflix.jobs", "netflix.jp",
		"netflix.ki", "netflix.kn", "netflix.kr", "netflix.kz", "netflix.la",
		"netflix.lc", "netflix.lu", "netflix.ly", "netflix.md", "netflix.mg",
		"netflix.ml", "netflix.mn", "netflix-service.com",
		"netflix-theater.com", "netflix-theatre.com", "netflix.net",
		"netflix.org"),

		'paxful' : ("paxful.com"),

		'paypal' : ("paypal.com", "paypal.com", "paypal.com.au", "paypal.at", "paypal.be",
		"paypal.ca", "paypal.fr", "paypal.de", "paypal.com.hk", "paypal.it",
		"paypal.com.mx", "paypal.nl", "paypal.pl", "paypal.com.sg", "paypal.es",
		"paypal.ch", "paypal.co.uk"),

		'protonmail' : ("protonmail.com", "protonmail.ch"),

		'rabobank' : ("rabobank.com", "rabobank.nl"),

		'skype' : ("skype.com", "skype.net", "skype.org"),

		'slack' : ("slack.com"),

		'sparkasse' : ("sparkasse.de", "s.de"),

		'spotify' : ("spotify.com", "spotify.org", "spotify.it", "spotify.de", "spotify.fr",
		"spotify.nl", "spotify.es", "spotify.se", "spotify.no", "spotify.fi",
		"spotify.ru", "spotify.lt", "spotify.be", "spotify.pt", "spotify.net"),

		'suntrust' : ("suntrust.com", "livesolid.com", "suntrustcreditcard.com", "suntrustmortgage.com",
		"suntrustmarine.com", "mysuntrustloan.com"),

		'telegram' : ("telegram.com", "telegram.org"),

		'twitter' : ("twitter.com", "ads-twitter.com"),

		'whatsapp' : ("whatsapp.com", "whatsapp.org", "whatsapp.net"),

		'yahoo' : ("yahoo.com", "ymail.com", "rocketmail.com", "yahoo.co.uk", "yahoo.fr",
		"yahoo.com.br", "yahoo.co.in", "yahoo.ca", "yahoo.com.ar", "yahoo.com.cn",
		"yahoo.com.mx", "yahoo.co.kr", "yahoo.co.nz", "yahoo.com.hk",
		"yahoo.com.sg", "yahoo.es", "yahoo.gr", "yahoo.de", "yahoo.com.ph",
		"yahoo.com.tw", "yahoo.dk", "yahoo.ie", "yahoo.it", "yahoo.se",
		"yahoo.com.au", "yahoo.co.id", "yahoo.cl", "yahoo.co.jp", "yahoo.co.th",
		"yahoo.com.co", "yahoo.com.my", "yahoo.com.tr", "yahoo.com.ve",
		"yahoo.com.vn", "yahoo.in", "yahoo.nl", "yahoo.no", "yahoo.pl",
		"yahoo.ro", "yahoo.net")}

try:
	sql_q_db = '''
		CREATE TABLE IF NOT EXISTS "brand_table" (
					"sha1"	string,
					"brand"	string
				);'''
	conn_hit.execute(sql_q_db)
	sql_q_db = '''
		ALTER TABLE "search_result_text" ADD COLUMN hit string'''
	conn_hit.execute(sql_q_db)
	sql_q_db = '''
		ALTER TABLE "search_result_image" ADD COLUMN hit string'''
	conn_hit.execute(sql_q_db)
	conn_hit.commit()
except sqlite3.Error as er:
	print("Issue creating table")

conn_hit.execute("UPDATE search_result_text SET HIT = NULL")
conn_hit.execute("UPDATE search_result_image SET HIT = NULL")
conn_hit.execute("DELETE FROM brand_table")
conn_hit.commit()

cursor_hit = conn_hit.cursor();
cursor_url = conn_url.cursor();

hash_list = cursor_hit.execute("SELECT DISTINCT filepath from screen_info").fetchall()
print("Populating brand translation table")
cnt = 0
all_hashes = set()
hash_dict = dict()
for ehash in hash_list:
	#brand_from_db = cursor_url.execute(f"select brand from urls where sha1 = '{ehash[0]}' and (blacklist IS NULL or blacklist = '') and (error_code IS NULL or error_code = 0) and brand <> ''").fetchall()
	brand_from_db = cursor_url.execute(f"select brand from urls where sha1 = '{ehash[0]}' and brand <> ''").fetchall()
	if not brand_from_db:
		continue
	conn_hit.execute("INSERT INTO brand_table (sha1, brand) VALUES (?, ?)", (ehash[0], brand_from_db[0][0]))
	conn_hit.commit()
	all_hashes.add(ehash[0])
	hash_dict[ehash[0]] = brand_from_db[0][0]
	cnt += 1
	print(f"{cnt} - {ehash[0]} - {brand_from_db[0][0]}", end="          \r")
print("\nFinished populating translation table")

def find_hits(tablename, region):
	print(f"Starting on: {tablename}")
	returnset = set()
	searched_url_list = cursor_hit.execute(f"select filepath from {tablename} group by filepath").fetchall()
	count = 0
	for searched_url in searched_url_list:
		baseurl_from_db = conn_hit.execute(f"select brand from brand_table where sha1 = '{searched_url[0]}'").fetchall()
		if not baseurl_from_db:
			continue
		if baseurl_from_db[0][0] in whitelist:
			baseurl = whitelist[baseurl_from_db[0][0]]
		else:
			continue
		hit = None

		if not region:
			searched_dns_list = cursor_hit.execute(f"select result, entry  from {tablename} where filepath = '{searched_url[0]}'").fetchall()
		else:
			searched_dns_list = cursor_hit.execute(f"select result, entry, region from {tablename} where filepath = '{searched_url[0]}'").fetchall()


		for url in searched_dns_list:
			url_fix = urlparse(url[0]).netloc

			sanlist = []
			sanlist.append([url_fix])
			# get SAN
			try:
				context = ssl.create_default_context()
				with socket.create_connection((url_fix, 443), timeout=2) as sock:
					with context.wrap_socket(sock, server_hostname=url_fix) as ssock:
						cert = ssock.getpeercert()
						sAN = defaultdict(list)
						for type_, san in cert['subjectAltName']:
							sAN[type_].append(san)
						sanlist.append(sAN['DNS'])
			except:
				print('Error in SAN for ' + str(url_fix))
			
			for searchurl in list(chain.from_iterable(sanlist)):
				if (len(searchurl) < 3):
					continue
				if searchurl.endswith(baseurl):
					hit = url_fix
					returnset.add(searched_url[0])
					if not region:
						conn_hit.execute(f"UPDATE {tablename} SET hit=? WHERE entry=? AND filepath=?", (hit, url[1], searched_url[0]))
					else:
						conn_hit.execute(f"UPDATE {tablename} SET hit=? WHERE entry=? AND region=? AND filepath=?", (hit, url[1], url[2], searched_url[0]))
					conn_hit.commit()
		count += 1
		print(f"{searched_url[0]} - {str(count)}", end="\r")
	print(f"\nEnded handling: {tablename}")
	return returnset

image_hits = find_hits("search_result_image", True)
text_hits = find_hits("search_result_text", False)

# remove dupes
image_hits = list(dict.fromkeys(image_hits))
text_hits = list(dict.fromkeys(text_hits))

print("Creating file for label checking")
''' DISABLED INDIV FILE CREATION DUE TO NOT USING THEM.
with open("all-but-not-image.txt", "w") as f:
	for eh in (all_hashes-image_hits):
		f.write(f"{eh} - {hash_dict[eh]}\n")
with open("all-but-not-text.txt", "w") as f:
	for eh in (all_hashes-text_hits):
		f.write(f"{eh} - {hash_dict[eh]}\n")
'''
##with open("all.txt", "w") as f:
##	for eh in ((all_hashes-text_hits)-image_hits):
##		f.write(f"{hash_dict[eh]} - {eh}\n")
len_benign = 510
len_phishing = 949
print(f"Total: {949}")
print(f"Hits from image: {len(image_hits)} ({len(image_hits)/949*100}%)")
print(f"Hits from text: {len(text_hits)} ({len(text_hits)/949*100}%)")
print(f"Hits from image+text: {len(text_hits.union(image_hits))} ({len(text_hits.union(image_hits))/949*100}%)")
print(f"Hits from intersect image-text: {len(text_hits.union(image_hits)-text_hits)} ({len(text_hits.union(image_hits)-text_hits)/949*100}%)")

print(f"Hits only image had: {len(image_hits-text_hits)} ({len(image_hits-text_hits)/949*100}%)")
print(f"Hits only text had: {len(text_hits-image_hits)} ({len(text_hits-image_hits)/949*100}%)")
