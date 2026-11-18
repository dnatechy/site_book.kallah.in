"""Environment-driven configuration; credentials never belong in Git."""
import os


class Config:
    SITE_URL = os.environ.get("BOOK_SITE_URL", "https://book.kallah.in").rstrip("/")
    JSON_SORT_KEYS = False
    SECRET_KEY = os.environ.get("BOOK_SECRET_KEY")  # Required before authenticated features.
