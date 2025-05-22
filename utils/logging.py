import sys
import os
from loguru import logger

def setup_logging():
    """Konfiguracja systemu logowania."""
    # Tworzenie katalogu na logi jeśli nie istnieje
    os.makedirs("logs", exist_ok=True)
    
    # Usunięcie domyślnego handlera
    logger.remove()
    
    # Dodanie handlera do konsoli
    logger.add(
        sys.stderr,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
        level="DEBUG"
    )
    
    # Dodanie handlera do pliku
    logger.add(
        "logs/app.log",
        rotation="1 day",
        retention="7 days",
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
        level="DEBUG"
    )
    
    logger.info("System logowania skonfigurowany") 