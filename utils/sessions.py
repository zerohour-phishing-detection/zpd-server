import sqlite3
from datetime import datetime
import tldextract


class Sessions():

    conn_storage = None
    shared = False
    storage = None

    def __init__(self, storage, shared=False):
        self.conn_storage = sqlite3.connect(storage)
        self.shared = shared
        self.setup_storage()
        self.storage = storage

        # delete unfinished tasks on start-up
        self.conn_storage.execute(f"DELETE FROM session WHERE result = 'processing'")
        self.conn_storage.commit()
        self.conn_storage.close()

    def store_state(self, uuid, url, result, state):
        if self.get_state(uuid, url) == 'new':
            self.conn_storage = sqlite3.connect(self.storage)
            self.conn_storage.execute(f"INSERT INTO session(uuid, timestamp, url, tld, result, state) VALUES ('{uuid}', '{datetime.now()}', '{url}', '{tldextract.extract(url).registered_domain}', '{result}', '{state}')")
        else:
            self.conn_storage = sqlite3.connect(self.storage)
            self.conn_storage.execute(f"UPDATE session SET result = '{result}', timestamp = '{datetime.now()}', state = '{state}' where uuid = '{uuid}' and url = '{url}'")
        self.conn_storage.commit()
        self.conn_storage.close()

    def get_state(self, uuid, url):
        if self.shared:
            sql_q_db = f'''
                select result, state, timestamp from session where url = "{url}" 
                '''
        else:
            sql_q_db = f'''
                select result, state, timestamp from session where uuid = "{uuid}" and url = "{url}" 
                '''
        self.conn_storage = sqlite3.connect(self.storage)
        result = self.conn_storage.execute(sql_q_db).fetchone()
        self.conn_storage.close()
        if result == None:
            return 'new'
        else:
            return result

    def setup_storage(self):
        try:
            sql_q_db = '''
                CREATE TABLE IF NOT EXISTS "session" (
                            "uuid"	string,
                            "timestamp" string,
                            "url"	string,
                            "tld"	string,
                            "result" string,
                            "state" string
                        );'''
            self.conn_storage.execute(sql_q_db)
            self.conn_storage.commit()
        except sqlite3.Error as er:
            self._main_logger.error("Failed to create session table")
            self._main_logger.error(er)