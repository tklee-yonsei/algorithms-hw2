import http.client
import threading
import unittest
from urllib.parse import urlencode

from src.hash_table import horner_hash
from src.server import ShortenerHTTPServer


class ServerTests(unittest.TestCase):
    def setUp(self):
        self.server = ShortenerHTTPServer(("127.0.0.1", 0))
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        self.connection = http.client.HTTPConnection("127.0.0.1", self.server.server_port)

    def tearDown(self):
        self.connection.close()
        self.server.shutdown()
        self.server.server_close()
        self.thread.join()

    def test_post_shorten_then_get_redirect(self):
        original_url = "https://example.com/a?x=1&y=two"
        self.connection.request(
            "POST",
            "/shorten",
            body=original_url.encode("utf-8"),
            headers={
                "Content-Type": "text/plain",
                "Host": "localhost:8000",
                "X-Forwarded-Proto": "https",
                "X-Forwarded-Host": "shortener.example.test",
            },
        )
        response = self.connection.getresponse()
        self.assertEqual(response.status, 200)
        short_url = response.read().decode("utf-8")
        self.assertEqual(short_url, "https://shortener.example.test/r/0")

        self.connection.request("GET", "/r/0")
        response = self.connection.getresponse()
        self.assertEqual(response.status, 302)
        self.assertEqual(response.getheader("Location"), original_url)

    def test_list_shows_all_short_urls_with_forwarded_host(self):
        host_headers = {
            "Host": "localhost:8000",
            "X-Forwarded-Proto": "https",
            "X-Forwarded-Host": "shortener.example.test",
        }
        for url in ("https://example.com/first", "https://example.com/second"):
            self.connection.request(
                "POST",
                "/shorten",
                body=url.encode("utf-8"),
                headers={"Content-Type": "text/plain", **host_headers},
            )
            response = self.connection.getresponse()
            self.assertEqual(response.status, 200)
            response.read()

        self.connection.request("GET", "/list", headers=host_headers)
        response = self.connection.getresponse()
        self.assertEqual(response.status, 200)
        page = response.read().decode("utf-8")
        self.assertIn("https://shortener.example.test/r/0", page)
        self.assertIn("https://shortener.example.test/r/1", page)
        self.assertIn("https://example.com/first", page)
        self.assertIn("https://example.com/second", page)

    def test_table_page_shows_buckets_and_collision_chains(self):
        urls = ("https://example.com/a", "https://example.com/i")
        self.assertEqual(horner_hash(urls[0], 8), horner_hash(urls[1], 8))
        for url in urls:
            self.connection.request(
                "POST",
                "/shorten",
                body=url.encode("utf-8"),
                headers={"Content-Type": "text/plain"},
            )
            response = self.connection.getresponse()
            self.assertEqual(response.status, 200)
            response.read()

        self.connection.request("GET", "/table")
        response = self.connection.getresponse()
        self.assertEqual(response.status, 200)
        page = response.read().decode("utf-8")
        self.assertIn("개별 체이닝 방식입니다.", page)
        self.assertIn("입력한 원본 URL을 키로 호너 해시를 계산", page)
        self.assertIn("h = (h * 31 + ord(문자)) % capacity", page)
        self.assertIn("2개 항목 / 8개 슬롯", page)
        expected_bucket = horner_hash(urls[0], 8)
        self.assertIn(f"<th scope=\"row\">{expected_bucket}</th>", page)
        self.assertIn("2개 노드", page)
        self.assertIn("URL 키: https://example.com/a", page)
        self.assertIn("URL 키: https://example.com/i", page)
        self.assertIn("짧은 코드: 0", page)
        self.assertIn("짧은 코드: 1", page)
        self.assertIn("ord(", page)

    def test_homepage_form_shortens_and_redirects_using_forwarded_address(self):
        self.connection.request("GET", "/")
        response = self.connection.getresponse()
        self.assertEqual(response.status, 200)
        self.assertIn(b'<form action="/shorten" method="post">', response.read())

        original_url = "https://example.com/from-form"
        host = "shortener.example.test"
        self.connection.request(
            "POST",
            "/shorten",
            body=urlencode({"url": original_url}),
            headers={
                "Content-Type": "application/x-www-form-urlencoded",
                "Host": host,
                "X-Forwarded-Proto": "https",
            },
        )
        response = self.connection.getresponse()
        self.assertEqual(response.status, 200)
        short_url = "https://shortener.example.test/r/0"
        self.assertIn(short_url.encode(), response.read())

        self.connection.request("GET", "/r/0", headers={"Host": host})
        response = self.connection.getresponse()
        self.assertEqual(response.status, 302)
        self.assertEqual(response.getheader("Location"), original_url)

    def test_invalid_form_url_returns_html_bad_request(self):
        self.connection.request(
            "POST",
            "/shorten",
            body=urlencode({"url": "not a URL"}),
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
        response = self.connection.getresponse()
        self.assertEqual(response.status, 400)
        self.assertTrue(response.getheader("Content-Type").startswith("text/html"))
        self.assertIn("올바른 URL".encode(), response.read())

    def test_invalid_url_returns_bad_request(self):
        self.connection.request("POST", "/shorten", body=b"not a URL")
        response = self.connection.getresponse()
        self.assertEqual(response.status, 400)

    def test_unknown_code_and_path_return_not_found(self):
        for path in ("/r/unknown", "/missing"):
            with self.subTest(path=path):
                self.connection.request("GET", path)
                response = self.connection.getresponse()
                self.assertEqual(response.status, 404)
                response.read()


if __name__ == "__main__":
    unittest.main()
