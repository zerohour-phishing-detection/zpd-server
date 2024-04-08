import sqlite3
from datetime import datetime

import tldextract


# TODO make abstract? can allow for different kinds of storage (in-memory, sqlite database file, mysql database, etc)
class SessionStorage:
    """
    The storage interface for all current sessions.

    Note that, currently, once a session has completed, it will not be deleted from the database.
    """

    shared = False
    storage = None

    def __init__(self, db_path, shared=True):
        self.shared = shared
        self.storage = db_path

        storage_conn = sqlite3.connect(db_path)
        self._setup_storage(storage_conn)

        # Delete unfinished tasks on start-up
        storage_conn.execute("DELETE FROM session WHERE result = 'processing'")
        storage_conn.commit()
        storage_conn.close()

    def _store_state(self, uuid, url, result, state):
        """
        Stores the given state (uuid, url, result, state) in the database.
        """
        storage_conn = sqlite3.connect(self.storage)

        now = datetime.now()
        if self._get_state(uuid, url) is None:
            domain = tldextract.extract(url).registered_domain

            storage_conn.execute(
                "INSERT INTO session (uuid, timestamp, url, tld, result, state) VALUES (?, ?, ?, ?, ?, ?)",
                [uuid, now, url, domain, result, state],
            )
        else:
            storage_conn.execute(
                "UPDATE session SET result = ?, timestamp = ?, state = ? WHERE uuid = ? AND url = ?",
                [result, now, state, uuid, url],
            )

        storage_conn.commit()
        storage_conn.close()

    def _get_state(self, uuid, url):
        """
        Retrieves the current State from the database, or None in case it is not present.
        """
        storage_conn = sqlite3.connect(self.storage)

        if self.shared:
            cursor = storage_conn.execute(
                "SELECT result, state, timestamp FROM session WHERE url = ?", [url]
            )
        else:
            cursor = storage_conn.execute(
                "SELECT result, state, timestamp FROM session WHERE uuid = ? AND url = ?",
                [uuid, url],
            )

        query_res = cursor.fetchone()
        storage_conn.close()

        if query_res is None:
            return None

        return State(result=query_res[0], state=query_res[1], timestamp=query_res[2])

    def _setup_storage(self, storage_conn):
        sql_q_db = """
            CREATE TABLE IF NOT EXISTS "session" (
                "uuid"	string,
                "timestamp" string,
                "url"	string,
                "tld"	string,
                "result" string,
                "state" string
            );"""
        storage_conn.execute(sql_q_db)
        storage_conn.commit()

    def get_session(self, uuid, url) -> "Session":
        # TODO persist session objects up to a limit for performance improvements, in combination with state cache
        return Session(self, uuid, url)


class State:
    result: str
    state: str
    timestamp = None

    def __init__(self, result, state, timestamp=None):
        self.result = result
        self.state = state
        self.timestamp = timestamp


class Session:
    """
    Represents a single session, i.e.
    """

    storage: SessionStorage
    uuid: str
    url: str

    def __init__(self, storage, uuid, url):
        self.storage = storage
        self.uuid = uuid
        self.url = url

    # TODO make 'result' some sort of enum (phishing, not phishing, inconclusive, processing)
    # also better names for the result,state
    def set_state(self, result, state):
        """
        Sets the state of this session to the given result and state.
        """
        return self.storage._store_state(self.uuid, self.url, result, state)

    def get_state(self):
        """
        Retrieves the current State of this session.
        """
        # TODO cache state in Session object (updates with set_state), but needs assurance of no outside influence (one Session instance per uuid-url pair)
        return self.storage._get_state(self.uuid, self.url)
