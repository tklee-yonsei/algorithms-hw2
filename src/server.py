"""HTTP server for the in-memory URL shortener."""

import argparse
from html import escape
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import parse_qsl, urlsplit

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

    def _send_html(self, status: int, body: str) -> None:
        encoded_body = body.encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(encoded_body)))
        self.end_headers()
        self.wfile.write(encoded_body)

    def _short_url(self, code: str) -> str:
        forwarded_proto = self.headers.get("X-Forwarded-Proto", "http")
        scheme = forwarded_proto.split(",", 1)[0].strip().lower()
        if scheme not in ("http", "https"):
            scheme = "http"
        host = self.headers.get("Host", "localhost:8000")
        return f"{scheme}://{host}/r/{code}"

    def do_POST(self) -> None:
        if urlsplit(self.path).path != "/shorten":
            self._send_text(404, "Not Found")
            return

        is_form = self.headers.get_content_type() == "application/x-www-form-urlencoded"
        content_length = self.headers.get("Content-Length")
        try:
            length = int(content_length) if content_length is not None else 0
            if length < 0:
                raise ValueError("negative Content-Length")
            body = self.rfile.read(length)
            if len(body) != length:
                raise ValueError("incomplete request body")
            decoded_body = body.decode("utf-8")
            if is_form:
                form_fields = parse_qsl(decoded_body, keep_blank_values=True)
                url = next((value for name, value in form_fields if name == "url"), "")
            else:
                url = decoded_body
            code = self.server.shortener.shorten(url)
        except (UnicodeDecodeError, ValueError):
            if is_form:
                self._send_html(400, self._error_page("올바른 URL을 입력해 주세요."))
                return
            self._send_text(400, "Bad Request")
            return

        if is_form:
            short_url = escape(self._short_url(code), quote=True)
            self._send_html(200, self._result_page(short_url))
            return

        self._send_text(200, f"http://localhost:8000/r/{code}")

    def do_GET(self) -> None:
        path = urlsplit(self.path).path
        if path == "/":
            self._send_html(200, self._form_page())
            return

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

    @staticmethod
    def _form_page() -> str:
        return (
            "<!doctype html><html lang=\"ko\"><meta charset=\"utf-8\">"
            "<meta name=\"viewport\" content=\"width=device-width, initial-scale=1\">"
            "<title>URL 단축기</title><body><main>"
            "<h1>URL 단축기</h1>"
            "<form action=\"/shorten\" method=\"post\">"
            "<label for=\"url\">줄일 URL</label> "
            "<input id=\"url\" name=\"url\" type=\"url\" required "
            "placeholder=\"https://example.com\"> "
            "<button type=\"submit\">줄이기</button>"
            "</form></main></body></html>"
        )

    @staticmethod
    def _result_page(short_url: str) -> str:
        return (
            "<!doctype html><html lang=\"ko\"><meta charset=\"utf-8\">"
            "<meta name=\"viewport\" content=\"width=device-width, initial-scale=1\">"
            "<title>짧은 링크</title><body><main>"
            "<h1>짧은 링크가 준비됐어요</h1>"
            f"<p><a href=\"{short_url}\">{short_url}</a></p>"
            "<p><a href=\"/\">다른 URL 줄이기</a></p>"
            "</main></body></html>"
        )

    @staticmethod
    def _error_page(message: str) -> str:
        return (
            "<!doctype html><html lang=\"ko\"><meta charset=\"utf-8\">"
            "<title>URL을 확인해 주세요</title><body><main>"
            f"<h1>{escape(message)}</h1><p><a href=\"/\">돌아가기</a></p>"
            "</main></body></html>"
        )


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
