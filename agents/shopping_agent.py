from a2a.types import AgentCard, AgentCapabilities, AgentSkill
from a2a.server.agent_execution import AgentExecutor, RequestContext
from a2a.server.events import EventQueue
from a2a.utils import new_agent_text_message
from typing_extensions import override
from duckduckgo_search import DDGS

class ShoppingAgent(AgentExecutor):
    def __init__(self, host="localhost", port=8002):
        self.agent_card = AgentCard(
            name="shopping-agent",
            description="Agent wyszukujący produkty w internecie.",
            version="0.1.0",
            url=f"http://{host}:{port}",
            documentationUrl="https://example.com/shopping-agent/docs",
            capabilities=AgentCapabilities(
                streaming=True,
                pushNotifications=True,
                stateTransitionHistory=False
            ),
            defaultInputModes=["text/plain"],
            defaultOutputModes=["text/plain"],
            skills=[
                AgentSkill(
                    id="product-search",
                    name="Wyszukiwanie produktów",
                    description="Wyszukuje produkty w internecie na podstawie zapytania użytkownika.",
                    tags=["search", "shopping", "products"],
                    examples=[
                        "Znajdź najnowszego iPhone'a.",
                        "Szukam laptopa do 3000 zł."
                    ],
                    inputModes=["text/plain"],
                    outputModes=["text/plain"]
                )
            ]
        )
        super().__init__()
        self.ddgs = DDGS()

    @override
    async def execute(self, context: RequestContext, event_queue: EventQueue) -> None:
        user_message = context.message.parts[0].text
        results = list(self.ddgs.text(user_message, max_results=3))
        if results:
            response = "\n".join([f"{r['title']} - {r['href']}" for r in results])
        else:
            response = "Nie znaleziono wyników."
        event_queue.enqueue_event(new_agent_text_message(response))

    @override
    async def cancel(self, context: RequestContext, event_queue: EventQueue) -> None:
        raise Exception('cancel not supported')

    async def start(self):
        await self.executor.serve()

    async def stop(self):
        pass 