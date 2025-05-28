import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from a2a.server.apps import A2AStarletteApplication
from a2a.server.request_handlers import DefaultRequestHandler
from a2a.server.tasks import InMemoryTaskStore
from agents.orchestrator.agent import OrchestratorAgent
import uvicorn
from fastapi import FastAPI, Request
from fastapi.responses import StreamingResponse
import json

# Initialize agent and request handler
agent = OrchestratorAgent()
request_handler = DefaultRequestHandler(
    agent_executor=agent,
    task_store=InMemoryTaskStore(),
)

# Create A2A application
a2a_app = A2AStarletteApplication(agent_card=agent.agent_card, http_handler=request_handler)

# Create FastAPI app and mount A2A app
app = FastAPI()
app.mount("/", a2a_app.build())

@app.post("/stream")
async def stream_endpoint(request: Request):
    body = await request.json()
    message = body["params"]["message"]
    context = request_handler.create_context_from_message(message)
    event_queue = request_handler.create_event_queue(context)

    async def event_generator():
        await agent.stream(context, event_queue)
        async for event in event_queue:
            yield f"data: {json.dumps(event)}\r\n\r\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000) 