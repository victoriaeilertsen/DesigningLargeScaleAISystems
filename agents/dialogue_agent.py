from a2a.types import AgentCard, AgentCapabilities, AgentSkill
from a2a.server.agent_execution import AgentExecutor, RequestContext
from a2a.server.events import EventQueue
from a2a.utils import new_agent_text_message
from typing_extensions import override
import re

class DialogueAgent(AgentExecutor):
    def __init__(self, host="localhost", port=8001):
        self.agent_card = AgentCard(
            name="dialogue-agent",
            description="Agent conducting dialogue with the user and determining intentions.",
            version="0.1.0",
            url=f"http://{host}:{port}",
            documentationUrl="https://example.com/dialogue-agent/docs",
            capabilities=AgentCapabilities(
                streaming=True,
                pushNotifications=True,
                stateTransitionHistory=False
            ),
            defaultInputModes=["text/plain"],
            defaultOutputModes=["text/plain"],
            skills=[
                AgentSkill(
                    id="dialogue",
                    name="User Dialogue",
                    description="Conducts conversation and recognizes user intentions.",
                    tags=["dialogue", "intent-detection"],
                    examples=[
                        "Hello, how can I help you?",
                        "I would like to buy a laptop."
                    ],
                    inputModes=["text/plain"],
                    outputModes=["text/plain"]
                )
            ]
        )
        super().__init__()

    @override
    async def execute(self, context: RequestContext, event_queue: EventQueue) -> None:
        user_message = context.message.parts[0].text
        if re.search(r"(kupi|znajd|szukaj|zamów|order|buy|find)", user_message, re.IGNORECASE):
            response = f"You want to find or buy something: '{user_message}'. Forwarding to shopping agent."
        else:
            response = f"Echo: {user_message}"
        event_queue.enqueue_event(new_agent_text_message(response))

    @override
    async def cancel(self, context: RequestContext, event_queue: EventQueue) -> None:
        raise Exception('cancel not supported') 