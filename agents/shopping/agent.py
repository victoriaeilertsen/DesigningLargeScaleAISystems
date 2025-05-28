from a2a.types import AgentCard, AgentCapabilities, AgentSkill, TaskStatus, TaskState, TaskArtifactUpdateEvent, Artifact, Part, TextPart
from a2a.server.agent_execution import AgentExecutor, RequestContext
from a2a.server.events import EventQueue
from typing_extensions import override
import asyncio
import os
import logging
import uuid

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

from utils.a2a_utils import (
    create_task_status,
    create_message,
    create_streaming_message,
    create_task_status_event,
    create_artifact
)
from utils.errors import ValidationError, TaskNotFoundError
from .prompts import SHOPPING_AGENT_SYSTEM_PROMPT

# --- LANGCHAIN IMPORTS ---
from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain
from langchain_google_genai import ChatGoogleGenerativeAI

class ShoppingAgent(AgentExecutor):
    def __init__(self):
        logger.debug("Initializing ShoppingAgent")
        
        # Debug environment variables
        api_key = os.getenv("GOOGLE_API_KEY")
        logger.debug(f"GOOGLE_API_KEY exists: {bool(api_key)}")
        logger.debug(f"GOOGLE_API_KEY length: {len(api_key) if api_key else 0}")
        if api_key:
            logger.debug(f"GOOGLE_API_KEY first 10 chars: {api_key[:10]}")
        
        self.agent_card = AgentCard(
            name="shopping-agent",
            description="Agent searching for products on the internet.",
            version="0.1.0",
            url="http://localhost:8002",
            documentationUrl="https://example.com/shopping-agent/docs",
            capabilities=AgentCapabilities(
                streaming=True,
                pushNotifications=True,
                stateTransitionHistory=True
            ),
            defaultInputModes=["text/plain", "application/json"],
            defaultOutputModes=["text/plain", "application/json"],
            skills=[
                AgentSkill(
                    id="product-search",
                    name="Product Search",
                    description="Searches for products on the internet based on user query.",
                    tags=["search", "shopping", "products"],
                    examples=[
                        "Find the latest iPhone.",
                        "I'm looking for a laptop under 3000."
                    ],
                    inputModes=["text/plain", "application/json"],
                    outputModes=["text/plain", "application/json"]
                )
            ]
        )
        self.system_prompt = SHOPPING_AGENT_SYSTEM_PROMPT
        # --- LANGCHAIN SETUP ---
        logger.debug("Setting up LangChain components")
        self.prompt = PromptTemplate(
            input_variables=["user_message"],
            template="You are a shopping assistant. User wants: {user_message}"
        )
        
        try:
            logger.debug("Initializing ChatGoogleGenerativeAI (Gemini)")
            self.llm = ChatGoogleGenerativeAI(
                api_key=api_key,
                model="gemini-1.5-flash"
            )
            # Test LLM initialization
            logger.debug("Testing Gemini LLM with simple prompt")
            test_response = self.llm.invoke("test")
            logger.debug(f"Gemini LLM test response: {test_response}")
            logger.debug("Gemini LLM initialization successful")
        except Exception as e:
            logger.error(f"Error initializing Gemini LLM: {str(e)}")
            raise
        
        self.chain = LLMChain(llm=self.llm, prompt=self.prompt)
        logger.debug("ShoppingAgent initialization completed")
        super().__init__()

    @override
    async def execute(self, context: RequestContext, event_queue: EventQueue) -> None:
        try:
            logger.debug("Starting execute method")
            
            # Validate input
            if not context.message.parts:
                logger.error("No message parts found")
                raise ValidationError("Message must contain at least one part")

            # Update task status to running
            logger.debug("Enqueueing task status: working")
            try:
                event_queue.enqueue_event(create_task_status_event(
                    context.task_id,
                    create_task_status(TaskState.working)
                ))
            except Exception as e:
                logger.error(f"Enqueue failed (working): {type(e).__name__}: {e}")
                raise

            # Get message
            user_message = context.message.parts[0].root.text
            logger.debug(f"Processing message: {user_message}")

            # --- LANGCHAIN EXECUTION ---
            logger.debug("Starting LLM execution")
            try:
                response = await asyncio.get_event_loop().run_in_executor(
                    None, 
                    lambda: self.chain.invoke({
                        "user_message": user_message
                    })
                )
                logger.debug(f"LLM response received: {response}")
                logger.debug("Enqueueing streaming message")
                try:
                    event_queue.enqueue_event(create_streaming_message(response))
                except Exception as e:
                    logger.error(f"Enqueue failed (streaming): {type(e).__name__}: {e}")
                    raise
            except Exception as e:
                logger.error(f"Error in LLM execution: {str(e)}")
                raise

            # Update task status to completed
            logger.debug("Enqueueing task status: completed")
            try:
                event_queue.enqueue_event(create_task_status_event(
                    context.task_id,
                    create_task_status(TaskState.completed)
                ))
            except Exception as e:
                logger.error(f"Enqueue failed (completed): {type(e).__name__}: {e}")
                raise
            logger.debug("Execute method completed successfully")

        except Exception as e:
            logger.error(f"Error in execute method: {str(e)}")
            # Update task status to failed
            logger.debug("Enqueueing task status: failed")
            try:
                event_queue.enqueue_event(create_task_status_event(
                    context.task_id,
                    create_task_status(TaskState.failed, str(e))
                ))
            except Exception as e2:
                logger.error(f"Enqueue failed (failed): {type(e2).__name__}: {e2}")
                raise
            raise

    @override
    async def stream(self, context: RequestContext, event_queue: EventQueue) -> None:
        logger.info("=== [SHOPPING STREAM CALLED] ===")
        try:
            logger.debug("Enqueueing task status: working")
            event_queue.enqueue_event(create_task_status_event(
                context.task_id,
                create_task_status(TaskState.working)
            ))

            user_message = context.message.parts[0].root.text
            logger.debug(f"Processing message (stream): {user_message}")

            response = await asyncio.get_event_loop().run_in_executor(
                None, 
                lambda: self.chain.invoke({
                    "user_message": user_message
                })
            )
            logger.debug(f"LLM response received (stream): {response}")

            # Tworzymy Artifact i TaskArtifactUpdateEvent zgodnie z A2A
            part = Part(root=TextPart(kind='text', metadata=None, text=response if isinstance(response, str) else response.get("text", str(response))))
            artifact = Artifact(
                artifactId=str(uuid.uuid4()),
                name="shopping_response",
                parts=[part]
            )
            logger.info(f"Artifact name: {artifact.name}, text: {artifact.parts[0].root.text}")
            event = TaskArtifactUpdateEvent(
                contextId=context.context_id,
                taskId=context.task_id,
                artifact=artifact
            )
            # Logujemy artifact i event tuż przed wysłaniem
            logger.debug(f"Artifact przed wysłaniem: {artifact}")
            logger.debug(f"Event przed wysłaniem: {event}")
            # Asercja: sprawdzamy, czy artifact i part są poprawne
            assert artifact.parts, "Artifact nie może być pusty"
            assert artifact.parts[0].root.text, "Part nie może być pusty"
            event_queue.enqueue_event(event)

            logger.debug("Enqueueing task status: completed")
            event_queue.enqueue_event(create_task_status_event(
                context.task_id,
                create_task_status(TaskState.completed)
            ))

        except Exception as e:
            logger.error(f"Error in stream method: {str(e)}")
            event_queue.enqueue_event(create_task_status_event(
                context.task_id,
                create_task_status(TaskState.failed, str(e))
            ))
            raise

    @override
    async def cancel(self, context: RequestContext, event_queue: EventQueue) -> None:
        logger.debug("Enqueueing task status: cancelled")
        try:
            event_queue.enqueue_event(create_task_status_event(
                context.task_id,
                create_task_status(TaskState.cancelled)
            ))
        except Exception as e:
            logger.error(f"Enqueue failed (cancelled): {type(e).__name__}: {e}")
            raise

    async def start(self):
        await self.serve()

    async def stop(self):
        pass