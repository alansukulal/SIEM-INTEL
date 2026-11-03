
import ipaddress
import socket
from html.parser import HTMLParser
from urllib.parse import urljoin, urlparse

import requests
from tavily import TavilyClient

from app.config import settings


# --------------------------------------------------
# Configuration
# --------------------------------------------------

REQUEST_TIMEOUT = 15
MAX_RESPONSE_SIZE = 1_000_000  # 1 MB
MAX_SCRAPE_CHARS = 12_000
MAX_REDIRECTS = 3

USER_AGENT = "SIEM-INTEL/1.0"


# --------------------------------------------------
# HTML Text Extractor
# --------------------------------------------------

class WebPageParser(HTMLParser):
    """Extract readable text and page title from HTML."""

    BLOCKED_TAGS = {
        "script",
        "style",
        "noscript",
        "svg",
        "iframe",
        "nav",
        "footer",
        "header",
    }

    def __init__(self):
        super().__init__()
        self.skip_depth = 0
        self.title_depth = 0
        self.title_parts = []
        self.text_parts = []

    def handle_starttag(self, tag, attrs):
        if tag in self.BLOCKED_TAGS:
            self.skip_depth += 1
            return

        if tag == "title":
            self.title_depth += 1

    def handle_endtag(self, tag):
        if tag in self.BLOCKED_TAGS:
            self.skip_depth = max(0, self.skip_depth - 1)
            return

        if tag == "title":
            self.title_depth = max(0, self.title_depth - 1)

        if tag in {"p", "div", "br", "li", "h1", "h2", "h3"}:
            self.text_parts.append("\n")

    def handle_data(self, data):
        if self.skip_depth:
            return

        cleaned = data.strip()

        if not cleaned:
            return

        if self.title_depth:
            self.title_parts.append(cleaned)

        self.text_parts.append(cleaned)

    def get_result(self):
        return {
            "title": " ".join(self.title_parts),
            "text": " ".join(self.text_parts),
        }



# URL Safety Validation


def validate_url(url: str) -> str:
    """
    Allow only public HTTP/HTTPS URLs.
    Reject localhost, private IPs and unsafe ports.
    """

    if not isinstance(url, str) or not url.strip():
        raise ValueError("A valid URL is required.")

    parsed = urlparse(url.strip())

    if parsed.scheme not in {"http", "https"}:
        raise ValueError("Only HTTP and HTTPS URLs are allowed.")

    if not parsed.hostname:
        raise ValueError("URL must contain a hostname.")

    if parsed.username or parsed.password:
        raise ValueError("URLs containing credentials are not allowed.")

    hostname = parsed.hostname.lower().rstrip(".")

    if hostname == "localhost" or hostname.endswith(".localhost"):
        raise ValueError("Localhost URLs are not allowed.")

    try:
        port = parsed.port
    except ValueError as exc:
        raise ValueError("Invalid URL port.") from exc

    allowed_port = 443 if parsed.scheme == "https" else 80

    if port is not None and port != allowed_port:
        raise ValueError("Only standard HTTP/HTTPS ports are allowed.")

    try:
        addresses = socket.getaddrinfo(
            hostname,
            port or allowed_port,
            type=socket.SOCK_STREAM,
        )
    except socket.gaierror as exc:
        raise ValueError("Unable to resolve URL hostname.") from exc

    if not addresses:
        raise ValueError("Hostname did not resolve to an IP address.")

    for address in addresses:
        ip = ipaddress.ip_address(address[4][0])

        if not ip.is_global:
            raise ValueError(
                "URLs resolving to private or non-public IP addresses "
                "are not allowed."
            )

    return url.strip()


# --------------------------------------------------
# Web Search - Tavily
# --------------------------------------------------

def web_search(
    query: str,
    max_results: int = 5,
    search_depth: str = "basic",
) -> dict:
    """
    Search external webpages using Tavily.

    Args:
        query: Search query.
        max_results: Number of results (1-10).
        search_depth: basic or advanced.
    """

    if not settings.tavily_api_key:
        raise RuntimeError("Tavily API key is not configured.")

    if not query or not query.strip():
        raise ValueError("Search query cannot be empty.")

    if not 1 <= max_results <= 10:
        raise ValueError("max_results must be between 1 and 10.")

    if search_depth not in {"basic", "advanced"}:
        raise ValueError("search_depth must be basic or advanced.")

    client = TavilyClient(api_key=settings.tavily_api_key)

    result = client.search(
        query=query.strip(),
        search_depth=search_depth,
        topic="general",
        max_results=max_results,
        include_answer=True,
        include_raw_content=False,
    )

    return result



# Web Scraping


def web_scrape(url: str) -> dict:
    """
    Fetch a public webpage and extract readable text.

    Redirect destinations are validated before fetching.
    Response size and request duration are bounded.
    """

    current_url = validate_url(url)
    headers = {
        "User-Agent": USER_AGENT,
        "Accept": "text/html,application/xhtml+xml",
    }

    for redirect_count in range(MAX_REDIRECTS + 1):

        response = requests.get(
            current_url,
            headers=headers,
            timeout=REQUEST_TIMEOUT,
            stream=True,
            allow_redirects=False,
        )

        try:
            # Handle redirects manually.
            if response.is_redirect:
                if redirect_count >= MAX_REDIRECTS:
                    raise RuntimeError("Maximum redirects exceeded.")

                location = response.headers.get("Location")

                if not location:
                    raise RuntimeError("Redirect has no destination.")

                current_url = validate_url(
                    urljoin(current_url, location)
                )
                continue

            response.raise_for_status()

            content_type = response.headers.get(
                "Content-Type", ""
            ).lower()

            if (
                "text/html" not in content_type
                and "application/xhtml+xml" not in content_type
            ):
                raise ValueError(
                    "URL does not return an HTML webpage."
                )

            content_length = response.headers.get("Content-Length")

            if content_length:
                if int(content_length) > MAX_RESPONSE_SIZE:
                    raise ValueError("Webpage exceeds the 1 MB limit.")

            content = bytearray()

            for chunk in response.iter_content(chunk_size=8192):
                content.extend(chunk)

                if len(content) > MAX_RESPONSE_SIZE:
                    raise ValueError("Webpage exceeds the 1 MB limit.")

            html = bytes(content).decode(
                response.encoding or "utf-8",
                errors="replace",
            )

            parser = WebPageParser()
            parser.feed(html)

            extracted = parser.get_result()

            text = extracted["text"][:MAX_SCRAPE_CHARS]

            if not text.strip():
                raise ValueError("No readable webpage content found.")

            return {
                "url": current_url,
                "title": extracted["title"],
                "content": text,
                "truncated": len(extracted["text"]) > MAX_SCRAPE_CHARS,
            }

        finally:
            response.close()

    raise RuntimeError("Unable to retrieve webpage.")
