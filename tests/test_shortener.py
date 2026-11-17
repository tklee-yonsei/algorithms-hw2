import unittest

from src.shortener import Shortener

VALID_URLS = (
    "http://example.com",
    "https://example.com",
    "https://example.com/path/to/page",
    "https://example.com/a-b_c.html",
    "https://example.com/search?q=hello&lang=ko",
    "https://example.com/%ED%95%9C%EA%B8%80?q=%EA%B0%80",
    "https://example.com/한글",
    "https://example.com/page#section-2",
    "http://localhost:8000/x",
    "https://user:pass@example.com:8443/p",
)

INVALID_URLS = (
    "",
    "   ",
    "example.com",
    "//example.com",
    "http://",
    "http:///path",
    "https://",
    "ftp://example.com",
    "file:///etc/passwd",
    "javascript:alert(1)",
    "mailto:a@example.com",
)


class ShortenTests(unittest.TestCase):
    def test_first_codes_follow_the_base62_counter(self):
        shortener = Shortener()
        self.assertEqual(shortener.shorten("https://example.com/0"), "0")
        self.assertEqual(shortener.shorten("https://example.com/1"), "1")
        self.assertEqual(shortener.shorten("https://example.com/2"), "2")

    def test_codes_cross_the_61_62_boundary(self):
        shortener = Shortener()
        codes = [shortener.shorten(f"https://example.com/{n}") for n in range(63)]
        self.assertEqual(codes[9], "9")
        self.assertEqual(codes[10], "a")
        self.assertEqual(codes[35], "z")
        self.assertEqual(codes[36], "A")
        self.assertEqual(codes[61], "Z")
        self.assertEqual(codes[62], "10")

    def test_codes_are_unique_across_many_urls(self):
        shortener = Shortener()
        codes = [shortener.shorten(f"https://example.com/{n}") for n in range(200)]
        self.assertEqual(sorted(codes), sorted(set(codes)))
        self.assertEqual(len(codes), 200)

    def test_same_url_returns_the_same_code(self):
        shortener = Shortener()
        first = shortener.shorten("https://example.com/a")
        shortener.shorten("https://example.com/b")
        again = shortener.shorten("https://example.com/a")
        self.assertEqual(first, again)

    def test_repeated_url_does_not_consume_a_code(self):
        shortener = Shortener()
        shortener.shorten("https://example.com/a")
        shortener.shorten("https://example.com/a")
        self.assertEqual(shortener.shorten("https://example.com/b"), "1")

    def test_urls_differing_only_slightly_get_different_codes(self):
        shortener = Shortener()
        codes = {
            shortener.shorten(url)
            for url in ("https://example.com", "https://example.com/", "http://example.com")
        }
        self.assertEqual(len(codes), 3)

    def test_valid_urls_are_accepted(self):
        for url in VALID_URLS:
            with self.subTest(url=url):
                self.assertIsInstance(Shortener().shorten(url), str)

    def test_invalid_urls_are_rejected(self):
        for url in INVALID_URLS:
            with self.subTest(url=url):
                with self.assertRaises(ValueError):
                    Shortener().shorten(url)

    def test_rejected_url_does_not_consume_a_code(self):
        shortener = Shortener()
        with self.assertRaises(ValueError):
            shortener.shorten("ftp://example.com")
        self.assertEqual(shortener.shorten("https://example.com"), "0")

    def test_non_string_urls_are_rejected(self):
        for url in (None, 123, b"https://example.com", ["https://example.com"]):
            with self.subTest(url=url):
                with self.assertRaises(TypeError):
                    Shortener().shorten(url)


class ExpandTests(unittest.TestCase):
    def test_expand_returns_the_original_url(self):
        shortener = Shortener()
        for url in VALID_URLS:
            with self.subTest(url=url):
                self.assertEqual(shortener.expand(shortener.shorten(url)), url)

    def test_expand_preserves_special_characters_exactly(self):
        shortener = Shortener()
        url = "https://example.com/a-b_c/%ED%95%9C?x=1&y=%20z#f"
        self.assertEqual(shortener.expand(shortener.shorten(url)), url)

    def test_expand_works_after_the_table_has_grown(self):
        shortener = Shortener()
        urls = [f"https://example.com/{n}" for n in range(100)]
        codes = [shortener.shorten(url) for url in urls]
        for url, code in zip(urls, codes):
            with self.subTest(code=code):
                self.assertEqual(shortener.expand(code), url)

    def test_unknown_code_is_not_found(self):
        shortener = Shortener()
        shortener.shorten("https://example.com")
        for code in ("1", "zzzz", "Z"):
            with self.subTest(code=code):
                with self.assertRaises(KeyError):
                    shortener.expand(code)

    def test_malformed_codes_are_not_found(self):
        shortener = Shortener()
        shortener.shorten("https://example.com")
        for code in ("", "!", "a b", "0/", "한글", None, 0):
            with self.subTest(code=code):
                with self.assertRaises(KeyError):
                    shortener.expand(code)

    def test_code_with_leading_zero_is_not_the_same_code(self):
        shortener = Shortener()
        shortener.shorten("https://example.com")
        with self.assertRaises(KeyError):
            shortener.expand("00")

    def test_expand_on_empty_shortener_is_not_found(self):
        with self.assertRaises(KeyError):
            Shortener().expand("0")


class StateTests(unittest.TestCase):
    def test_new_shortener_starts_over_like_a_restarted_server(self):
        old = Shortener()
        code = old.shorten("https://example.com/old")
        fresh = Shortener()
        with self.assertRaises(KeyError):
            fresh.expand(code)
        self.assertEqual(fresh.shorten("https://example.com/new"), "0")

    def test_two_instances_do_not_share_state(self):
        first, second = Shortener(), Shortener()
        first.shorten("https://example.com/first")
        self.assertEqual(second.shorten("https://example.com/second"), "0")
        self.assertEqual(second.expand("0"), "https://example.com/second")
        self.assertEqual(first.expand("0"), "https://example.com/first")


if __name__ == "__main__":
    unittest.main()
