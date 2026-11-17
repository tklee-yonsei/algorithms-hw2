"""URL shortener backed by the hand-written hash table."""

from urllib.parse import urlparse

from src.base62 import encode
from src.hash_table import HashTable


def _validate_url(url: str) -> None:
    if not isinstance(url, str):
        raise TypeError("url must be a string")
    # Whitespace and control characters would corrupt the Location header.
    if any(character.isspace() or ord(character) < 32 or ord(character) == 127 for character in url):
        raise ValueError("url must not contain whitespace or control characters")

    parsed = urlparse(url)
    if parsed.scheme not in ("http", "https") or not parsed.hostname:
        raise ValueError("url must be an absolute http(s) url with a host")


class Shortener:
    def __init__(self) -> None:
        self._table = HashTable()
        self._codes = HashTable()
        self._next_id = 0

    def shorten(self, url: str) -> str:
        _validate_url(url)

        try:
            return self._table.get(url)
        except KeyError:
            pass

        code = encode(self._next_id)
        self._next_id += 1
        self._table.put(url, code)
        self._codes.put(code, url)
        return code

    def expand(self, code: str) -> str:
        """Return the original url, or raise KeyError if the code is unknown."""
        return self._codes.get(code)

    def items(self):
        """Return the stored short-code and original-URL pairs."""
        return self._codes.items()

    def table_snapshot(self):
        """Return the current capacity, item count, and indexed slots."""
        return self._table.capacity, len(self._table), tuple(self._table.slots())
