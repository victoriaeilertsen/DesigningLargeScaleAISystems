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

# Loading environment variables
load_dotenv()

async def main():
    """Main application function."""
    try:
        # Logging configuration
        setup_logging()
        logger.info("Starting application...")
        
        # Initialize agents
        dialogue_agent = DialogueAgent(host="localhost", port=8001)
        shopping_agent = ShoppingAgent(host="localhost", port=8002)
        
        # Start agents
        await asyncio.gather(
            dialogue_agent.start(),
            shopping_agent.start()
        )
        
        logger.info("Application started successfully")
        
        # Main loop
        while True:
            await asyncio.sleep(1)
            
    except KeyboardInterrupt:
        logger.info("Received interrupt signal, stopping application...")
    except Exception as e:
        logger.error(f"An error occurred: {str(e)}")
    finally:
        # Stop agents
        try:
            await dialogue_agent.stop()
            await shopping_agent.stop()
            logger.info("Application stopped successfully")
        except Exception as e:
            logger.error(f"Error while stopping application: {str(e)}")

if __name__ == "__main__":
    asyncio.run(main())
