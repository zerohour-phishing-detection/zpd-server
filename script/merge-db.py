import os
import sys
import sqlite3
import argparse
from shutil import copyfile

parser = argparse.ArgumentParser()
parser.add_argument('--out', help='Assumes the output db to be empty!', required=True)
parser.add_argument('--in', nargs = '+', help='The sqlite file the search results are stored in')
args = parser.parse_args()

# Handle arguments
input_dbs = vars(args)['in']
output_db_str = args.out

# Copy the first input DB so we don't have to handle that one.
# Exit is first input argument DB doesn't exist
if not (os.path.exists(input_dbs[0])):
    print(f"Database argument '{input_dbs[0]}'' does not exist.\nAborted due to no destination DB.")
    sys.exit(-1)
copyfile(input_dbs[0], output_db_str)

# Create variables for output database
output_db_conn = sqlite3.connect(output_db_str)
output_db_curs = output_db_conn.cursor();

# Create empty set with handled hashes
handled_hash = set()

# Populate the set with hashes from the copied initial DB.
results = output_db_curs.execute("select distinct filepath from screen_info").fetchall()
for row in results:
	handled_hash.add(row[0])

# Done processing first DB.
print(f"Finished handling entries from DB: {input_dbs[0]}")

# Loop to handle any following databases.
totalentries = len(handled_hash)
db_handled = 1
duplicates = 0
skipped_db = 0
for input_db in input_dbs[1:]:
    # Verify that DB exists
    if not (os.path.exists(input_db)):
        skipped_db += 1
        #print(f"Database argument '{input_db}'' does not exist. Skipping to next DB")
        continue

    # Open DB connections
    output_db_curs.execute(f"ATTACH '{input_db}' as dba")

    # Loop over all entries
    results = output_db_curs.execute("select distinct filepath from dba.screen_info").fetchall()
    entry_cnt = 0
    for res in results:
        current_entry = res[0]
        print(f"[Total: {totalentries:<7}] [DB: {db_handled:<3} - {input_db:<40}] [{entry_cnt:<7}] - {current_entry:<100}", end="\r")

        # Verify if hash was already in a previous DB
        if current_entry in handled_hash:
            duplicates += 1
            #print(f"Already handled hash: {current_entry}. Skipping to next")
            continue
        handled_hash.add(current_entry)

        output_db_curs.execute("BEGIN")
        output_db_curs.execute(f"INSERT INTO screen_info SELECT * FROM dba.screen_info WHERE dba.screen_info.filepath = '{current_entry}'")
        output_db_curs.execute(f"INSERT INTO region_info SELECT * FROM dba.region_info WHERE dba.region_info.filepath = '{current_entry}'")
        output_db_curs.execute(f"INSERT INTO search_result_text SELECT * FROM dba.search_result_text WHERE dba.search_result_text.filepath = '{current_entry}'")
        output_db_curs.execute(f"INSERT INTO search_result_image SELECT * FROM dba.search_result_image WHERE dba.search_result_image.filepath = '{current_entry}'")
        output_db_conn.commit()
        entry_cnt += 1
        totalentries += 1

    # Close connection to avoid leaking filehandles on big merges
    output_db_curs.execute("detach database dba")
    db_handled += 1

print(f"\nDone merging databases!\nEntries handled: {totalentries}\nDB's handled: {db_handled}\nDB's skipped due to missing file: {skipped_db}\nEntries skipped due to duplicate: {duplicates}")
