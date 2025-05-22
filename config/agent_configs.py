from typing import Dict, Any

# Dialogue agent configuration
DIALOGUE_AGENT_CONFIG: Dict[str, Any] = {
    "name": "dialogue_agent",
    "description": "Agent responsible for conducting dialogue with the user and managing tasks",
    "capabilities": [
        "understand_user_needs",
        "manage_tasks",
        "coordinate_with_shopping_agent"
    ],
    "host": "localhost",
    "port": 8000
}

# Shopping agent configuration
SHOPPING_AGENT_CONFIG: Dict[str, Any] = {
    "name": "shopping_agent",
    "description": "Agent responsible for product search and purchase management",
    "capabilities": [
        "search_products",
        "compare_prices",
        "set_price_alerts",
        "manage_wishlist"
    ],
    "host": "localhost",
    "port": 8001
}

# All agents configuration
AGENT_CONFIGS = {
    "dialogue": DIALOGUE_AGENT_CONFIG,
    "shopping": SHOPPING_AGENT_CONFIG
} 