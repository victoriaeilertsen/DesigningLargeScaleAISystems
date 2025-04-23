"""
DuckDuckGo-based product search tool (no API key required).
Returns up to `k` web search results as dicts: {name, url, snippet}.
Later we can chain this with a price‑scraper tool to fetch exact prices.
"""
from typing import List, Dict
from langchain_community.tools import DuckDuckGoSearchRun

_ddg = DuckDuckGoSearchRun()

def search_products(query: str, k: int = 5) -> List[Dict]:
    """Search the web for products matching `query`."""
    raw_results = _ddg.invoke({"query": query})
    hits: List[Dict] = []
    for r in raw_results[:k]:
        hits.append({
            "name": r.get("title", r["url"]),
            "price": None,         # price to be filled by separate scraper
            "currency": None,
            "features": r.get("content", ""),
            "url": r["url"],
        })
    return hits