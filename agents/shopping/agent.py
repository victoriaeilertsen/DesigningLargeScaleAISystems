from a2a.types import AgentCard, AgentCapabilities, AgentSkill, TaskStatus, TaskState, TaskArtifactUpdateEvent, Artifact, Part, TextPart, Message, Role, TaskStatusUpdateEvent, Task
from a2a.server.agent_execution import AgentExecutor, RequestContext
from a2a.server.events import EventQueue
from a2a.server.tasks import InMemoryTaskStore
from typing_extensions import override
from typing import AsyncGenerator
import asyncio
import os
import logging
import uuid
from loguru import logger
from datetime import datetime, UTC

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
    def __init__(self, task_store: InMemoryTaskStore):
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
        self.task_store = task_store
        super().__init__()

    @override
    async def execute(self, context: RequestContext, event_queue: EventQueue) -> AsyncGenerator[TaskStatusUpdateEvent, None]:
        """Execute the shopping agent."""
        try:
            # Extract message text from context (handle both dict and object cases)
            message_text = ""
            for part in context.message.parts:
                if isinstance(part, dict):
                    if part.get('kind') == 'text':
                        message_text += part.get('text', '')
                else:
                    if getattr(part, 'kind', None) == 'text':
                        message_text += getattr(part, 'text', '')
            
            # Get or create task
            task = await self.task_store.get(context.task_id)
            if not task:
                task = Task(
                    id=context.task_id,
                    contextId=context.context_id,
                    status=TaskStatus(
                        state=TaskState.submitted,
                        timestamp=datetime.now(UTC).isoformat()
                    )
                )
                await self.task_store.save(task)
            
            # Update task status to working
            task.status = TaskStatus(
                state=TaskState.working,
                timestamp=datetime.now(UTC).isoformat()
            )
            await self.task_store.save(task)
            
            # Process message
            response = await self.chain.arun(message=message_text)
            logger.info(f"[SHOPPING] LLM response: {response}")
            
            # Create response message
            response_message = Message(
                messageId=str(uuid.uuid4()),
                role=Role.agent,
                parts=[TextPart(text=response if isinstance(response, str) else str(response))]
            )
            
            # Update task status to completed
            task.status = TaskStatus(
                state=TaskState.completed,
                message=response_message,
                timestamp=datetime.now(UTC).isoformat()
            )
            await self.task_store.save(task)
            
            event_queue.enqueue_event(TaskStatusUpdateEvent(
                contextId=context.context_id,
                taskId=context.task_id,
                status=task.status,
                final=True
            ))
                
        except Exception as e:
            logger.error(f"[SHOPPING] Error processing message: {str(e)}")
            error_message = Message(
                messageId=str(uuid.uuid4()),
                role=Role.agent,
                parts=[TextPart(text=str(e))]
            )
            if task:
                task.status = TaskStatus(
                    state=TaskState.failed,
                    message=error_message,
                    timestamp=datetime.now(UTC).isoformat()
                )
                await self.task_store.save(task)
            event_queue.enqueue_event(TaskStatusUpdateEvent(
                contextId=context.context_id,
                taskId=context.task_id,
                status={
                    "state": TaskState.failed.value,
                    "message": error_message,
                    "timestamp": datetime.now(UTC).isoformat()
                },
                final=True
            ))

    @override
    async def stream(self, context: RequestContext, event_queue: EventQueue) -> None:
        logger.info("=== [SHOPPING STREAM CALLED] ===")
        try:
            # Create and enqueue status update
            event_queue.enqueue_event(create_task_status_event(
                context.task_id,
                create_task_status(TaskState.working, timestamp=datetime.now(UTC).isoformat())
            ))
            
            # Simulate processing
            await asyncio.sleep(0.1)
            
            # Create and enqueue completion event
            event_queue.enqueue_event(create_task_status_event(
                context.task_id,
                create_task_status(TaskState.completed, timestamp=datetime.now(UTC).isoformat())
            ))

        except Exception as e:
            logger.error(f"Error in stream method: {str(e)}")
            event_queue.enqueue_event(create_task_status_event(
                context.task_id,
                create_task_status(TaskState.failed, str(e), timestamp=datetime.now(UTC).isoformat())
            ))
            raise

    @override
    async def cancel(self, context: RequestContext, event_queue: EventQueue) -> None:
        logger.debug("Enqueueing task status: cancelled")
        try:
            event_queue.enqueue_event(create_task_status_event(
                context.task_id,
                create_task_status(TaskState.cancelled, timestamp=datetime.now(UTC).isoformat())
            ))
        except Exception as e:
            logger.error(f"Enqueue failed (cancelled): {type(e).__name__}: {e}")
            raise

    async def start(self):
        await self.serve()

    async def stop(self):
        pass