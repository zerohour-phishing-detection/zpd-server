"""
Just some misc util functions that might be universally used
"""

import os
import time

from bs4 import BeautifulSoup

# Setup logging
from utils.logging import main_logger

logger = main_logger


def to_file(filename: str, string: str):
    with open(filename, "w") as f:
        f.write(string)


def time_format(inp):
    m, s = divmod(inp, 60)
    h, m = divmod(m, 60)
    return f"{h:2.0f}h {m:2.0f}m {s:5.2f}s"


def get_page_title(file_path):
    """
    Gets the HTML page title of a .html file given by its file path.

    Returns
    str or None
        The page title (str) if available, or None if it has no title.
    """
    with open(file_path, "r") as f:
        soup = BeautifulSoup(f, "html.parser")
        if soup.title and soup.title.string:
            return soup.title.string.strip()

        return None


def time_string(time_start, i, n):
    now = time.time()
    elapsed = now - time_start
    total_time_expected = max((elapsed / i) * (n - 1), elapsed)
    remaining_time = max(total_time_expected - elapsed, 0)
    return f"Elapsed: {time_format(elapsed)} - Remaining: {time_format(remaining_time)} - Expected: {time_format(total_time_expected)}"


def setstatus(status):
    to_file("logs/status.txt", status)
