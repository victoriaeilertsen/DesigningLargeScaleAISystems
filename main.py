import asyncio
import os
from dotenv import load_dotenv
from loguru import logger

from agents.specialized.dialogue_agent import get_dialogue_agent
from agents.specialized.shopping_agent import get_shopping_agent
from config.settings import setup_logging
from utils.helpers import construct_agent_url
from agents.dialogue_agent import DialogueAgent
from agents.shopping_agent import ShoppingAgent

# Ładowanie zmiennych środowiskowych
load_dotenv()

async def main():
    """Główna funkcja aplikacji."""
    try:
        # Konfiguracja logowania
        setup_logging()
        logger.info("Uruchamianie aplikacji...")
        
        # Inicjalizacja agentów
        dialogue_agent = DialogueAgent(host="localhost", port=8001)
        shopping_agent = ShoppingAgent(host="localhost", port=8002)
        
        # Uruchomienie agentów
        await asyncio.gather(
            dialogue_agent.start(),
            shopping_agent.start()
        )
        
        logger.info("Aplikacja uruchomiona pomyślnie")
        
        # Główna pętla
        while True:
            await asyncio.sleep(1)
            
    except KeyboardInterrupt:
        logger.info("Otrzymano sygnał przerwania, zatrzymywanie aplikacji...")
    except Exception as e:
        logger.error(f"Wystąpił błąd: {str(e)}")
    finally:
        # Zatrzymanie agentów
        try:
            await dialogue_agent.stop()
            await shopping_agent.stop()
            logger.info("Aplikacja zatrzymana pomyślnie")
        except Exception as e:
            logger.error(f"Błąd podczas zatrzymywania aplikacji: {str(e)}")

if __name__ == "__main__":
    asyncio.run(main())
