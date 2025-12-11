import requests
from bs4 import BeautifulSoup
import time
import random
from typing import Optional
from duckduckgo_search import DDGS

class SustainabilityScraper:
    """
    Web-scraping agent designed to:
    1. Locate an ESG or sustainability report for a given company.
    2. Extract readable textual content from that page.
    """

    def find_esg_url(self, ticker: str) -> str:
        """
        Searches DuckDuckGo for the most relevant ESG report URL.
        Returns an empty string if no suitable result is found.
        """
        query = f"{ticker} company sustainability report 2024 summary"
        print(f"[Agent] Running automatic search for: '{query}'...")

        try:
            # DDGS uses a context manager to manage sessions cleanly.
            with DDGS() as ddgs:
                results = list(ddgs.text(query, max_results=3))

            if results:
                best_url = results[0]["href"]
                print(f"[Agent] URL found: {best_url}")
                return best_url

            print("[Agent] No search results found.")
            return ""

        except Exception as e:
            print(f"[Agent] Search error: {e}")
            return ""

    def fetch_company_data(self, ticker: str, url: Optional[str] = None) -> str:
        """
        Full scraping workflow:
        - Performs ESG URL lookup if none is provided.
        - Fetches page content and extracts structured text.
        """
        target_url = url or self.find_esg_url(ticker)

        if not target_url:
            return "Error: Auto-discovery failed. No URL found."

        print(f"[Scraper] Fetching content from: {target_url}...")

        headers = {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/91.0.4472.124 Safari/537.36"
            )
        }

        try:
            # Random delay to avoid triggering bot protections.
            time.sleep(random.uniform(1, 3))

            response = requests.get(target_url, headers=headers, timeout=10)

            if response.status_code != 200:
                return f"Error: Access denied (HTTP {response.status_code}). The site may be protected."

            soup = BeautifulSoup(response.text, "html.parser")

            # Extracts readable text from common structural tags.
            text_blocks = []
            for tag in soup.find_all(["p", "h2", "h3", "li"]):
                txt = tag.get_text(strip=True)
                if len(txt) > 30:  # Filters out noise and very short items.
                    text_blocks.append(txt)

            full_text = " ".join(text_blocks)

            # Detects cases where content is JavaScript-rendered or empty.
            if len(full_text) < 200:
                return "Error: Page content appears empty or JS-rendered."

            print(f"[Scraper] Extracted {len(full_text)} characters.")
            return full_text[:12000]  # Caps payload size for LLM processing.

        except Exception as e:
            return f"Error scraping: {str(e)}"
