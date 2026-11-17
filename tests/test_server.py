import http.client
import threading
import unittest

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
            headers={"Content-Type": "text/plain"},
        )
        response = self.connection.getresponse()
        self.assertEqual(response.status, 200)
        short_url = response.read().decode("utf-8")
        self.assertEqual(short_url, "http://localhost:8000/r/0")

        self.connection.request("GET", "/r/0")
        response = self.connection.getresponse()
        self.assertEqual(response.status, 302)
        self.assertEqual(response.getheader("Location"), original_url)

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
