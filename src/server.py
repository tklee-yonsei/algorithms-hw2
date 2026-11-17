"""HTTP server for the in-memory URL shortener."""

import argparse
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import urlsplit

from src.shortener import Shortener


class ShortenerRequestHandler(BaseHTTPRequestHandler):
    def _send_text(self, status: int, body: str, location: str | None = None) -> None:
        encoded_body = body.encode("utf-8")
        self.send_response(status)
        if location is not None:
            self.send_header("Location", location)
        self.send_header("Content-Type", "text/plain; charset=utf-8")
        self.send_header("Content-Length", str(len(encoded_body)))
        self.end_headers()
        self.wfile.write(encoded_body)

    def do_POST(self) -> None:
        if urlsplit(self.path).path != "/shorten":
            self._send_text(404, "Not Found")
            return

        content_length = self.headers.get("Content-Length")
        try:
            length = int(content_length) if content_length is not None else 0
            if length < 0:
                raise ValueError("negative Content-Length")
            body = self.rfile.read(length)
            if len(body) != length:
                raise ValueError("incomplete request body")
            url = body.decode("utf-8")
            code = self.server.shortener.shorten(url)
        except (UnicodeDecodeError, ValueError):
            self._send_text(400, "Bad Request")
            return

        self._send_text(200, f"http://localhost:8000/r/{code}")

    def do_GET(self) -> None:
        path = urlsplit(self.path).path
        if not path.startswith("/r/"):
            self._send_text(404, "Not Found")
            return

        code = path[len("/r/") :]
        try:
            url = self.server.shortener.expand(code)
        except KeyError:
            self._send_text(404, "Not Found")
            return

        self._send_text(302, "", location=url)


class ShortenerHTTPServer(HTTPServer):
    shortener: Shortener

    def __init__(self, server_address: tuple[str, int]) -> None:
        super().__init__(server_address, ShortenerRequestHandler)
        self.shortener = Shortener()


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the URL shortener HTTP server.")
    parser.add_argument("--port", type=int, default=8000)
    args = parser.parse_args()

    with ShortenerHTTPServer(("0.0.0.0", args.port)) as server:
        print(f"Serving on http://localhost:{args.port}")
        try:
            server.serve_forever()
        except KeyboardInterrupt:
            pass


if __name__ == "__main__":
    main()
