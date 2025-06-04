from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import traceback
import logging
from agent import ShoppingAgent

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Shopping Assistant")

class Message(BaseModel):
    content: str

# Initialize the agent
try:
    agent = ShoppingAgent()
    logger.info("Shopping agent initialized successfully")
except Exception as e:
    logger.error(f"Failed to initialize Shopping agent: {str(e)}")
    raise

@app.post("/chat")
async def chat(message: Message):
    try:
        logger.info(f"Received message: {message.content}")
        response = agent.process_message(message.content)
        logger.info(f"Sending response: {response}")
        return {"response": response}
    except Exception as e:
        error_msg = f"Error processing message: {str(e)}"
        logger.error(error_msg)
        logger.error("Full traceback:")
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=error_msg)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8002) 