
import unittest
from unittest.mock import MagicMock, patch
import socket

from app.tools import web


class FakeResponse:
    def __init__(
        self,
        content,
        status_code=200,
        headers=None,
        encoding="utf-8",
        redirect=False,
    ):
        self.content = content
        self.status_code = status_code
        self.headers = headers or {
            "Content-Type": "text/html; charset=utf-8"
        }
        self.encoding = encoding
        self.is_redirect = redirect
        self.closed = False

    def iter_content(self, chunk_size=8192):
        yield self.content

    def raise_for_status(self):
        if self.status_code >= 400:
            raise Exception(f"HTTP error: {self.status_code}")

    def close(self):
        self.closed = True


def public_dns_result(*args, **kwargs):
    return [
        (
            socket.AF_INET,
            socket.SOCK_STREAM,
            6,
            "",
            ("93.184.216.34", 80),
        )
    ]


class URLValidationTests(unittest.TestCase):

    @patch("app.tools.web.socket.getaddrinfo", side_effect=public_dns_result)
    def test_valid_public_url(self, mock_dns):
        result = web.validate_url("https://example.com")

        self.assertEqual(result, "https://example.com")
        mock_dns.assert_called_once()

    def test_reject_localhost(self):
        with self.assertRaises(ValueError):
            web.validate_url("http://localhost")

    def test_reject_non_http_scheme(self):
        with self.assertRaises(ValueError):
            web.validate_url("ftp://example.com")

    def test_reject_credentials(self):
        with self.assertRaises(ValueError):
            web.validate_url("https://user:password@example.com")

    def test_reject_non_standard_port(self):
        with self.assertRaises(ValueError):
            web.validate_url("https://example.com:8080")

    @patch(
        "app.tools.web.socket.getaddrinfo",
        return_value=[
            (
                socket.AF_INET,
                socket.SOCK_STREAM,
                6,
                "",
                ("127.0.0.1", 80),
            )
        ],
    )
    def test_reject_private_ip(self, mock_dns):
        with self.assertRaises(ValueError):
            web.validate_url("http://example.com")


class WebScrapeTests(unittest.TestCase):

    @patch("app.tools.web.socket.getaddrinfo", side_effect=public_dns_result)
    @patch("app.tools.web.requests.get")
    def test_scrape_html_page(self, mock_get, mock_dns):
        html = b"""
        <html>
            <head>
                <title>Microsoft Sentinel Documentation</title>
                <script>secret_code()</script>
            </head>
            <body>
                <h1>Sentinel Troubleshooting</h1>
                <p>Check data connector health.</p>
            </body>
        </html>
        """

        response = FakeResponse(html)
        mock_get.return_value = response

        result = web.web_scrape(
            "https://example.com/documentation"
        )

        self.assertEqual(
            result["title"],
            "Microsoft Sentinel Documentation",
        )

        self.assertIn(
            "Sentinel Troubleshooting",
            result["content"],
        )

        self.assertIn(
            "Check data connector health.",
            result["content"],
        )

        self.assertNotIn(
            "secret_code",
            result["content"],
        )

        self.assertFalse(result["truncated"])
        self.assertTrue(response.closed)

    @patch("app.tools.web.socket.getaddrinfo", side_effect=public_dns_result)
    @patch("app.tools.web.requests.get")
    def test_reject_non_html_content(self, mock_get, mock_dns):
        mock_get.return_value = FakeResponse(
            b"some data",
            headers={"Content-Type": "application/json"},
        )

        with self.assertRaises(ValueError):
            web.web_scrape("https://example.com/data")

    @patch("app.tools.web.socket.getaddrinfo", side_effect=public_dns_result)
    @patch("app.tools.web.requests.get")
    def test_reject_large_content(self, mock_get, mock_dns):
        mock_get.return_value = FakeResponse(
            b"x" * (web.MAX_RESPONSE_SIZE + 1)
        )

        with self.assertRaises(ValueError):
            web.web_scrape("https://example.com/large")


class WebSearchTests(unittest.TestCase):

    @patch("app.tools.web.TavilyClient")
    @patch("app.tools.web.settings")
    def test_tavily_search(self, mock_settings, mock_client):
        mock_settings.tavily_api_key = "test-api-key"

        expected_result = {
            "results": [
                {
                    "title": "Sentinel Documentation",
                    "url": "https://example.com",
                }
            ]
        }

        mock_client.return_value.search.return_value = expected_result

        result = web.web_search(
            query="Microsoft Sentinel troubleshooting",
            max_results=5,
        )

        self.assertEqual(result, expected_result)

        mock_client.assert_called_once_with(
            api_key="test-api-key"
        )

    @patch("app.tools.web.settings")
    def test_search_without_api_key(self, mock_settings):
        mock_settings.tavily_api_key = None

        with self.assertRaises(RuntimeError):
            web.web_search("Sentinel troubleshooting")

    def test_reject_empty_query(self):
        with self.assertRaises(ValueError):
            web.web_search(" ")

    def test_reject_invalid_max_results(self):
        with self.assertRaises(ValueError):
            web.web_search("Sentinel", max_results=20)

    def test_reject_invalid_search_depth(self):
        with self.assertRaises(ValueError):
            web.web_search(
                "Sentinel",
                search_depth="invalid",
            )


if __name__ == "__main__":
    unittest.main(verbosity=2)
