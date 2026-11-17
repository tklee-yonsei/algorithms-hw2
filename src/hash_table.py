"""Separate-chaining hash table with a Horner string hash."""

from __future__ import annotations

_INITIAL_CAPACITY = 8
_MAX_LOAD = 0.7


def horner_hash(key: str, capacity: int) -> int:
    """Hash a string with Horner's rule: h = (h * 31 + ord(c)) % capacity."""
    h = 0
    for character in key:
        h = (h * 31 + ord(character)) % capacity
    return h


def horner_hash_steps(key: str, capacity: int):
    """Yield the previous hash, character, code point, and new hash per step."""
    h = 0
    for character in key:
        previous = h
        code_point = ord(character)
        h = (h * 31 + code_point) % capacity
        yield previous, character, code_point, h


class _Node:
    def __init__(self, key: str, value, next_node: _Node | None = None) -> None:
        self.key = key
        self.value = value
        self.next = next_node


class HashTable:
    """Maps string keys to values using a linked list in each bucket.

    With max_load=None the bucket array never grows.
    """

    def __init__(self, capacity: int = _INITIAL_CAPACITY, max_load: float | None = _MAX_LOAD) -> None:
        if capacity < 1:
            raise ValueError("capacity must be positive")
        self._buckets: list[_Node | None] = [None] * capacity
        self._size = 0
        self._max_load = max_load

    @property
    def capacity(self) -> int:
        return len(self._buckets)

    def __len__(self) -> int:
        return self._size

    def put(self, key: str, value) -> None:
        if not isinstance(key, str):
            raise TypeError("key must be a string")

        index = horner_hash(key, self.capacity)
        node = self._buckets[index]
        while node is not None:
            if node.key == key:
                node.value = value
                return
            node = node.next

        self._buckets[index] = _Node(key, value, self._buckets[index])
        self._size += 1
        if self._max_load is not None and self._size > self.capacity * self._max_load:
            self._grow()

    def get(self, key: str):
        if not isinstance(key, str):
            raise KeyError(key)

        node = self._buckets[horner_hash(key, self.capacity)]
        while node is not None:
            if node.key == key:
                return node.value
            node = node.next
        raise KeyError(key)

    def comparison_count(self, key: str) -> int:
        """Return the number of chain nodes inspected for a lookup."""
        index = horner_hash(key, self.capacity)
        comparisons = 0
        node = self._buckets[index]
        while node is not None:
            comparisons += 1
            if node.key == key:
                return comparisons
            node = node.next
        return comparisons

    def items(self):
        for head in self._buckets:
            node = head
            while node is not None:
                yield node.key, node.value
                node = node.next

    def slots(self):
        """Yield each bucket index and its chain as key-value pairs."""
        for index, head in enumerate(self._buckets):
            chain = []
            node = head
            while node is not None:
                chain.append((node.key, node.value))
                node = node.next
            yield index, tuple(chain)

    def _grow(self) -> None:
        old_entries = list(self.items())
        self._buckets = [None] * (self.capacity * 2)
        for key, value in old_entries:
            index = horner_hash(key, self.capacity)
            self._buckets[index] = _Node(key, value, self._buckets[index])
