"""
DuckDuckGo-based product search tool (no API key required).
Returns up to `k` web search results as dicts: {name, url, snippet}.
Later we can chain this with a price‑scraper tool to fetch exact prices.
"""
from typing import List, Dict
from langchain_community.utilities import DuckDuckGoSearchAPIWrapper

_ddg = DuckDuckGoSearchAPIWrapper()

def search_products(query: str, k: int = 5) -> List[Dict]:
    """Search the web for products matching `query`."""
    raw_results = _ddg.results(query, k)
    hits: List[Dict] = []
    for r in raw_results:
        hits.append({
            "name": r.get("title", r.get("link")),
            "price": None,          # price can be scraped later
            "currency": None,
            "features": r.get("snippet", ""),
            "url": r.get("link"),
        })
    return hits
