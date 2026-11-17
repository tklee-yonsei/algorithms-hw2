"""Open-addressing hash table with linear probing and a Horner string hash."""

_INITIAL_CAPACITY = 8
_MAX_LOAD = 0.7


def horner_hash(key: str, capacity: int) -> int:
    """Hash a string with Horner's rule: h = (h * 31 + ord(c)) % capacity."""
    h = 0
    for character in key:
        h = (h * 31 + ord(character)) % capacity
    return h


class HashTable:
    """Maps string keys to values. Entries cannot be deleted.

    With max_load=None the table never grows, so it can be filled up to its
    capacity. Callers must not insert more entries than the capacity.
    """

    def __init__(self, capacity: int = _INITIAL_CAPACITY, max_load: float | None = _MAX_LOAD) -> None:
        if capacity < 1:
            raise ValueError("capacity must be positive")
        self._slots = [None] * capacity
        self._size = 0
        self._max_load = max_load

    @property
    def capacity(self) -> int:
        return len(self._slots)

    def __len__(self) -> int:
        return self._size

    def put(self, key: str, value) -> None:
        if not isinstance(key, str):
            raise TypeError("key must be a string")

        index = self._find_slot(key)
        if index == -1:
            raise OverflowError("hash table is full")
        if self._slots[index] is not None:
            self._slots[index] = (key, value)
            return

        self._slots[index] = (key, value)
        self._size += 1
        if self._max_load is not None and self._size > self.capacity * self._max_load:
            self._grow()

    def get(self, key: str):
        if not isinstance(key, str):
            raise KeyError(key)

        index = self._find_slot(key)
        entry = self._slots[index] if index != -1 else None
        if entry is None:
            raise KeyError(key)
        return entry[1]

    def probe_count(self, key: str) -> int:
        """Return how many slots a lookup of key inspects.

        A found key counts the slot holding it; a missing key counts the empty
        slot that ends the search.
        """
        index = horner_hash(key, self.capacity)
        probes = 1
        while probes < self.capacity and self._slots[index] is not None and self._slots[index][0] != key:
            index = (index + 1) % self.capacity
            probes += 1
        return probes

    def items(self):
        for entry in self._slots:
            if entry is not None:
                yield entry

    def slots(self):
        """Yield each slot's index and entry, including empty slots."""
        for index, entry in enumerate(self._slots):
            yield index, entry

    def _find_slot(self, key: str) -> int:
        """Return the slot holding key, or the empty slot where it belongs."""
        index = horner_hash(key, self.capacity)
        for _ in range(self.capacity):
            if self._slots[index] is None or self._slots[index][0] == key:
                return index
            index = (index + 1) % self.capacity
        return -1

    def _grow(self) -> None:
        old_entries = list(self.items())
        self._slots = [None] * (self.capacity * 2)
        for key, value in old_entries:
            self._slots[self._find_slot(key)] = (key, value)
