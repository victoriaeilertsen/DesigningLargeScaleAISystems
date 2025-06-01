from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import traceback
import logging
from agent import ClassifierAgent

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Formal Professional Agent")

class Message(BaseModel):
    content: str

# Initialize the agent
try:
    agent = ClassifierAgent()
    logger.info("Classifier agent initialized successfully")
except Exception as e:
    logger.error(f"Failed to initialize Classifier agent: {str(e)}")
    raise

@app.post("/chat")
async def chat(message: Message):
    try:
        response = agent.process_message(message.content)
        return {"response": response}
    except Exception as e:
        logger.error(f"Error details: {str(e)}")
        logger.error("Full traceback:")
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001) 