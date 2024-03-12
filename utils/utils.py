"""
Just some misc util functions that might be universally used
"""

from bs4 import BeautifulSoup


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
