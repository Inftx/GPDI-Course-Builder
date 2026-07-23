import os
from datetime import datetime


def get_file_extension(filename):
    """Return the file extension in lowercase."""
    return os.path.splitext(filename)[1].lower()


def current_timestamp():
    """Return a formatted timestamp."""
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")