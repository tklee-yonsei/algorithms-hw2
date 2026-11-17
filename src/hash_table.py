"""Open-addressing hash table with linear probing and a Horner string hash."""

_INITIAL_CAPACITY = 8
_MAX_LOAD_PERCENT = 70


def horner_hash(key: str, capacity: int) -> int:
    """Hash a string with Horner's rule: h = (h * 31 + ord(c)) % capacity."""
    h = 0
    for character in key:
        h = (h * 31 + ord(character)) % capacity
    return h


class HashTable:
    """Maps string keys to values. Entries cannot be deleted."""

    def __init__(self) -> None:
        self._slots = [None] * _INITIAL_CAPACITY
        self._size = 0

    @property
    def capacity(self) -> int:
        return len(self._slots)

    def __len__(self) -> int:
        return self._size

    def put(self, key: str, value) -> None:
        if not isinstance(key, str):
            raise TypeError("key must be a string")

        index = self._find_slot(key)
        if self._slots[index] is not None:
            self._slots[index] = (key, value)
            return

        self._slots[index] = (key, value)
        self._size += 1
        if self._size * 100 > self.capacity * _MAX_LOAD_PERCENT:
            self._grow()

    def get(self, key: str):
        if not isinstance(key, str):
            raise KeyError(key)

        entry = self._slots[self._find_slot(key)]
        if entry is None:
            raise KeyError(key)
        return entry[1]

    def items(self):
        for entry in self._slots:
            if entry is not None:
                yield entry

    def _find_slot(self, key: str) -> int:
        """Return the slot holding key, or the empty slot where it belongs."""
        index = horner_hash(key, self.capacity)
        while self._slots[index] is not None and self._slots[index][0] != key:
            index = (index + 1) % self.capacity
        return index

    def _grow(self) -> None:
        old_entries = list(self.items())
        self._slots = [None] * (self.capacity * 2)
        for key, value in old_entries:
            self._slots[self._find_slot(key)] = (key, value)
