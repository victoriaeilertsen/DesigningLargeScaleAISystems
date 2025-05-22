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
        rotation="1 day",
        retention="7 days",
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
        level="DEBUG" if DEBUG else "INFO"
    )
    
    logger.info("Logging system configured") 