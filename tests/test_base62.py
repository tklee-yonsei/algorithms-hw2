import unittest

from src.base62 import decode, encode


class Base62Tests(unittest.TestCase):
    def test_encode_known_values(self):
        self.assertEqual(encode(0), "0")
        self.assertEqual(encode(9), "9")
        self.assertEqual(encode(10), "a")
        self.assertEqual(encode(35), "z")
        self.assertEqual(encode(36), "A")
        self.assertEqual(encode(61), "Z")
        self.assertEqual(encode(62), "10")
        self.assertEqual(encode(3844), "100")

    def test_decode_known_values(self):
        self.assertEqual(decode("0"), 0)
        self.assertEqual(decode("Z"), 61)
        self.assertEqual(decode("10"), 62)
        self.assertEqual(decode("100"), 3844)

    def test_round_trip_large_values(self):
        for value in (0, 1, 61, 62, 3844, 2**128):
            with self.subTest(value=value):
                self.assertEqual(decode(encode(value)), value)

    def test_encode_rejects_negative_and_non_integer_values(self):
        with self.assertRaises(ValueError):
            encode(-1)
        for value in (1.5, "62", True):
            with self.subTest(value=value):
                with self.assertRaises(TypeError):
                    encode(value)

    def test_decode_rejects_empty_and_invalid_input(self):
        for value in ("", "abc!", "안녕"):
            with self.subTest(value=value):
                with self.assertRaises(ValueError):
                    decode(value)
        with self.assertRaises(TypeError):
            decode(62)


if __name__ == "__main__":
    unittest.main()
