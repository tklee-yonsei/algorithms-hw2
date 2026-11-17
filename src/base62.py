"""Base-62 conversion using digits, lowercase letters, then uppercase letters."""

_ALPHABET = "0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ"


def encode(n: int) -> str:
    """Return the base-62 representation of a non-negative integer."""
    if not isinstance(n, int) or isinstance(n, bool):
        raise TypeError("n must be an integer")
    if n < 0:
        raise ValueError("n must be non-negative")
    if n == 0:
        return _ALPHABET[0]

    encoded = []
    while n:
        n, remainder = divmod(n, len(_ALPHABET))
        encoded.append(_ALPHABET[remainder])
    return "".join(reversed(encoded))


def decode(s: str) -> int:
    """Return the integer represented by a base-62 string."""
    if not isinstance(s, str):
        raise TypeError("s must be a string")
    if not s:
        raise ValueError("s must not be empty")

    value = 0
    for character in s:
        digit = _ALPHABET.find(character)
        if digit == -1:
            raise ValueError(f"invalid base-62 character: {character!r}")
        value = value * len(_ALPHABET) + digit
    return value
