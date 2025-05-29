import os
from dotenv import load_dotenv
from loguru import logger
import sys

# Loading environment variables
load_dotenv()

# Basic application settings
APP_NAME = os.getenv("APP_NAME", "A2A Shopping Assistant")
DEBUG = os.getenv("DEBUG", "False").lower() == "true"

# A2A settings
A2A_HOST = os.getenv("A2A_HOST", "localhost")
A2A_PORT = int(os.getenv("A2A_PORT", "8000"))
STREAMLIT_PORT = int(os.getenv("STREAMLIT_PORT", "8501"))

# Groq settings
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
if not GROQ_API_KEY:
    raise ValueError("GROQ_API_KEY is not set in environment variables")

# Agent configuration
AGENT_CONFIG = {
    "orchestrator": {
        "name": "orchestrator-agent",
        "url": os.getenv("ORCHESTRATOR_URL", "http://localhost:8000"),
        "port": int(os.getenv("ORCHESTRATOR_PORT", "8000")),
        "description": "Agent responsible for coordinating and routing requests to specialized agents."
    },
    "classifier": {
        "name": "classifier-agent",
        "url": os.getenv("CLASSIFIER_URL", "http://localhost:8001"),
        "port": int(os.getenv("CLASSIFIER_PORT", "8001")),
        "description": "Agent responsible for classifying user intents and general conversation."
    },
    "shopping": {
        "name": "shopping-agent",
        "url": os.getenv("SHOPPING_URL", "http://localhost:8002"),
        "port": int(os.getenv("SHOPPING_PORT", "8002")),
        "description": "Agent responsible for handling shopping-related requests."
    }
}

# API Keys
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
if not GOOGLE_API_KEY:
    logger.warning("GOOGLE_API_KEY not set in environment variables")

# Frontend configuration
FRONTEND_CONFIG = {
    "debug_mode": os.getenv("DEBUG_MODE", "false").lower() == "true",
    "max_debug_log_entries": int(os.getenv("MAX_DEBUG_LOG_ENTRIES", "30"))
}

# Task configuration
TASK_CONFIG = {
    "max_retries": int(os.getenv("MAX_TASK_RETRIES", "3")),
    "retry_delay": int(os.getenv("TASK_RETRY_DELAY", "1")),  # seconds
    "timeout": int(os.getenv("TASK_TIMEOUT", "30"))  # seconds
}

def setup_logging():
    """Logging system configuration."""
    # Remove default handler
    logger.remove()
    
    # Add console handler
    logger.add(
        sys.stderr,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
        level="DEBUG" if DEBUG else "INFO"
    )
    
    # Add file handler
    logger.add(
        "logs/app.log",
        rotation="500 MB",
        retention="10 days",
        level="DEBUG",
        format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {message}"
    )
    
    logger.info("Logging system configured") 