import csv
import time


class Archive:
    """
    Utility for storing detection checks in a CSV database.
    """
    filename: str

    def __init__(self, filename):
        self.filename = filename

    def append(self, uuid, url, settings, result):
        """
        Adds the given entry to the archive.
        """
        row = [uuid, url, time.time(), settings, result]

        with open(self.filename, 'a', newline='') as file:
            writer = csv.writer(file)
            writer.writerow(row)
