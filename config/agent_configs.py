from typing import Dict, Any

# Konfiguracja agenta dialogowego
DIALOGUE_AGENT_CONFIG: Dict[str, Any] = {
    "name": "dialogue_agent",
    "description": "Agent odpowiedzialny za prowadzenie dialogu z użytkownikiem i zarządzanie zadaniami",
    "capabilities": [
        "understand_user_needs",
        "manage_tasks",
        "coordinate_with_shopping_agent"
    ],
    "host": "localhost",
    "port": 8000
}

# Konfiguracja agenta zakupowego
SHOPPING_AGENT_CONFIG: Dict[str, Any] = {
    "name": "shopping_agent",
    "description": "Agent odpowiedzialny za wyszukiwanie produktów i zarządzanie zakupami",
    "capabilities": [
        "search_products",
        "compare_prices",
        "set_price_alerts",
        "manage_wishlist"
    ],
    "host": "localhost",
    "port": 8001
}

# Konfiguracja wszystkich agentów
AGENT_CONFIGS = {
    "dialogue": DIALOGUE_AGENT_CONFIG,
    "shopping": SHOPPING_AGENT_CONFIG
} 