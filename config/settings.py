import os
from dotenv import load_dotenv
from loguru import logger
import sys

# Ładowanie zmiennych środowiskowych
load_dotenv()

# Podstawowe ustawienia aplikacji
APP_NAME = os.getenv("APP_NAME", "A2A Shopping Assistant")
DEBUG = os.getenv("DEBUG", "False").lower() == "true"

# Ustawienia A2A
A2A_HOST = os.getenv("A2A_HOST", "localhost")
A2A_PORT = int(os.getenv("A2A_PORT", "8000"))
STREAMLIT_PORT = int(os.getenv("STREAMLIT_PORT", "8501"))

# Ustawienia Groq
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
if not GROQ_API_KEY:
    raise ValueError("GROQ_API_KEY nie jest ustawiony w zmiennych środowiskowych")

def setup_logging():
    """Konfiguracja systemu logowania."""
    # Usunięcie domyślnego handlera
    logger.remove()
    
    # Dodanie handlera do konsoli
    logger.add(
        sys.stderr,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
        level="DEBUG" if DEBUG else "INFO"
    )
    
    # Dodanie handlera do pliku
    logger.add(
        "logs/app.log",
        rotation="1 day",
        retention="7 days",
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
        level="DEBUG" if DEBUG else "INFO"
    )
    
    logger.info("System logowania skonfigurowany") 