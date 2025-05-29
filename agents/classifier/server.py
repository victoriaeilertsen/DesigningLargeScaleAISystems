import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from a2a.server.apps import A2AStarletteApplication
from a2a.server.request_handlers import DefaultRequestHandler
from a2a.server.tasks import InMemoryTaskStore
from agents.classifier.agent import ClassifierAgent
import uvicorn
from fastapi import FastAPI
from loguru import logger

# Initialize FastAPI app
app = FastAPI()

# Initialize task store and request handler
task_store = InMemoryTaskStore()
agent = ClassifierAgent(task_store)
request_handler = DefaultRequestHandler(
    agent_executor=agent,
    task_store=task_store
)

# Create A2A application and mount it under /a2a
a2a_app = A2AStarletteApplication(agent_card=agent.agent_card, http_handler=request_handler)
app.mount("/a2a", a2a_app.build())

@app.get("/")
async def health_check():
    """Health check endpoint."""
    return {"status": "ok"}

if __name__ == "__main__":
    logger.info("[CLASSIFIER] Starting server on port 8001")
    uvicorn.run(app, host="0.0.0.0", port=8001) 