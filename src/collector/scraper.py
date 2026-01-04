# -------------------------------------------------
# HTTP client used to fetch web pages
# -------------------------------------------------
import requests

# -------------------------------------------------
# HTML parsing library
# Used to extract readable text from web pages
# -------------------------------------------------
from bs4 import BeautifulSoup

# -------------------------------------------------
# Utilities for delays and randomness
# Used to reduce risk of being blocked by websites
# -------------------------------------------------
import time
import random

# -------------------------------------------------
# Typing utilities
# -------------------------------------------------
from typing import Optional

# -------------------------------------------------
# DuckDuckGo search client
# Used to find ESG / sustainability report URLs
# -------------------------------------------------
from duckduckgo_search import DDGS


class SustainabilityScraper:
    """
    Utility class responsible for retrieving sustainability-related text.

    This class does NOT analyze or score ESG.
    It only:
    - finds a relevant public web page
    - extracts readable text
    """

    def find_esg_url(self, ticker: str) -> str:
        """
        Searches the web for a sustainability or ESG report.

        Why this exists:
        - company ESG pages are not standardized
        - URLs change frequently
        - we need a best-effort automatic discovery
        """

        # Build a generic search query.
        # Using natural language improves search relevance.
        query = f"{ticker} company sustainability report 2024 summary"

        # Log search action for traceability
        print(f"[Agent] Running automatic search for: '{query}'...")

        try:
            # DuckDuckGo search session.
            # Context manager ensures proper resource cleanup.
            with DDGS() as ddgs:
                results = list(ddgs.text(query, max_results=3))

            # If at least one result is found,
            # assume the first one is the most relevant.
            if results:
                best_url = results[0]["href"]
                print(f"[Agent] URL found: {best_url}")
                return best_url

            # No usable result found
            print("[Agent] No search results found.")
            return ""

        except Exception as e:
            # Catch network, parsing or API errors
            print(f"[Agent] Search error: {e}")
            return ""

    def fetch_company_data(self, ticker: str, url: Optional[str] = None) -> str:
        """
        Complete scraping pipeline.

        Steps:
        1. Discover ESG page URL (if not provided)
        2. Download HTML content
        3. Extract readable text
        4. Return a capped text payload
        """

        # Use provided URL if available.
        # Otherwise, attempt automatic discovery.
        target_url = url or self.find_esg_url(ticker)

        # If no URL can be found, abort early.
        if not target_url:
            return "Error: Auto-discovery failed. No URL found."

        print(f"[Scraper] Fetching content from: {target_url}...")

        # Custom User-Agent header.
        # Many websites block default Python user agents.
        headers = {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/91.0.4472.124 Safari/537.36"
            )
        }

        try:
            # Random delay before request.
            # Reduces chance of being detected as a bot.
            time.sleep(random.uniform(1, 3))

            # Perform HTTP GET request.
            response = requests.get(
                target_url,
                headers=headers,
                timeout=10
            )

            # Reject non-success HTTP responses.
            # 403 and 429 are common when scraping.
            if response.status_code != 200:
                return (
                    f"Error: Access denied (HTTP {response.status_code}). "
                    "The site may be protected."
                )

            # Parse HTML content
            soup = BeautifulSoup(response.text, "html.parser")

            # Container for extracted text blocks
            text_blocks = []

            # Extract text from commonly meaningful tags.
            # We ignore scripts, nav bars, footers, etc.
            for tag in soup.find_all(["p", "h2", "h3", "li"]):

                # Clean and normalize text
                txt = tag.get_text(strip=True)

                # Filter out very short fragments (menus, breadcrumbs, etc.)
                if len(txt) > 30:
                    text_blocks.append(txt)

            # Concatenate all extracted blocks
            full_text = " ".join(text_blocks)

            # Detect pages with little or no usable content.
            # This often happens with JavaScript-rendered sites.
            if len(full_text) < 200:
                return "Error: Page content appears empty or JS-rendered."

            print(f"[Scraper] Extracted {len(full_text)} characters.")

            # Limit payload size.
            # Large texts are expensive and unnecessary for downstream processing.
            return full_text[:12000]

        except Exception as e:
            # Catch network errors, timeouts, parsing failures
            return f"Error scraping: {str(e)}"
