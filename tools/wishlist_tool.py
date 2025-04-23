"""
Wishlist tool – persist user picks and price‑alert thresholds.
Data is stored in JSON under memory/wishlist.json.
"""
import json
from pathlib import Path
from typing import Dict, List, Optional

WISHLIST_PATH = Path(__file__).parent.parent / "memory" / "wishlist.json"
WISHLIST_PATH.parent.mkdir(parents=True, exist_ok=True)


def _load() -> List[Dict]:
    if WISHLIST_PATH.exists():
        with open(WISHLIST_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    return []


def _save(data: List[Dict]) -> None:
    with open(WISHLIST_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def add_to_wishlist(product: Dict, alert_price: Optional[float] = None) -> None:
    entry = product.copy()
    if alert_price is not None:
        entry["alert_price"] = alert_price
    wishlist = _load()
    wishlist.append(entry)
    _save(wishlist)


def list_wishlist() -> List[Dict]:
    return _load()
