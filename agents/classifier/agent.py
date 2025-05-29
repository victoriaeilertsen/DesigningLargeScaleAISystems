from a2a.types import AgentCard, AgentCapabilities, AgentSkill, TaskStatus, TaskState, TaskArtifactUpdateEvent, Artifact, Part, TextPart, Message, Role, TaskStatusUpdateEvent, Task
from a2a.server.agent_execution import AgentExecutor, RequestContext
from a2a.server.events import EventQueue
from a2a.server.tasks import InMemoryTaskStore
from typing_extensions import override
import re
import asyncio
import os
import logging
import uuid
import json
from loguru import logger
from datetime import datetime, UTC
from typing import AsyncGenerator

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
from .prompts import CLASSIFIER_AGENT_SYSTEM_PROMPT

# --- LANGCHAIN IMPORTS ---
from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain
from langchain_google_genai import ChatGoogleGenerativeAI

class ClassifierAgent(AgentExecutor):
    def __init__(self, task_store: InMemoryTaskStore):
        logger.debug("Initializing ClassifierAgent")
        
        # Debug environment variables
        api_key = os.getenv("GOOGLE_API_KEY")
        logger.debug(f"GOOGLE_API_KEY exists: {bool(api_key)}")
        logger.debug(f"GOOGLE_API_KEY length: {len(api_key) if api_key else 0}")
        if api_key:
            logger.debug(f"GOOGLE_API_KEY first 10 chars: {api_key[:10]}")
        
        self.agent_card = AgentCard(
            name="classifier-agent",
            description="Agent analyzing user intentions and needs.",
            version="0.1.0",
            url="http://localhost:8001",
            documentationUrl="https://example.com/classifier-agent/docs",
            capabilities=AgentCapabilities(
                streaming=True,
                pushNotifications=True,
                stateTransitionHistory=True
            ),
            defaultInputModes=["text/plain", "application/json"],
            defaultOutputModes=["text/plain", "application/json"],
            skills=[
                AgentSkill(
                    id="intent-classification",
                    name="Intent Classification",
                    description="Analyzes user messages to determine intentions and needs.",
                    tags=["classification", "intent-detection", "needs-analysis"],
                    examples=[
                        "I want to buy a laptop",
                        "What's the weather like?",
                        "Add this to my wishlist"
                    ],
                    inputModes=["text/plain", "application/json"],
                    outputModes=["text/plain", "application/json"]
                )
            ]
        )
        self.system_prompt = CLASSIFIER_AGENT_SYSTEM_PROMPT
        
        # --- LANGCHAIN SETUP ---
        logger.debug("Setting up LangChain components")
        self.prompt = PromptTemplate(
            input_variables=["user_message"],
            template="Respond to the user's message: {user_message}"
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
        logger.debug("ClassifierAgent initialization completed")
        self.task_store = task_store
        super().__init__()

    @override
    async def stream(self, context: RequestContext, event_queue: EventQueue) -> None:
        logger.info("=== [CLASSIFIER STREAM CALLED] ===")
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
            logger.debug(f"LLM response received: {response}")

            # Parse the response as JSON
            try:
                classification = json.loads(response['text'])
                logger.debug(f"Parsed classification: {classification}")
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse LLM response as JSON: {e}")
                raise ValidationError("Invalid response format from classifier")

            # Create artifact with classification results
            artifact = Artifact(
                artifactId=str(uuid.uuid4()),
                name="classifier_response",
                parts=[Part(root=TextPart(
                    kind='text',
                    metadata=None,
                    text=json.dumps(classification)
                ))]
            )
            
            # Log the artifact before sending
            logger.debug(f"Created artifact: {artifact}")
            logger.info(f"Artifact name: {artifact.name}, text: {artifact.parts[0].root.text}")
            
            # Create and send the event
            event = TaskArtifactUpdateEvent(
                contextId=context.context_id,
                taskId=context.task_id,
                artifact=artifact
            )
            logger.debug(f"Created event: {event}")
            
            # Validate artifact before sending
            assert artifact.parts, "Artifact must have at least one part"
            assert artifact.parts[0].root.text, "Artifact part text cannot be empty"
            
            event_queue.enqueue_event(event)
            logger.debug("Enqueued classification event")

            # Update task status to completed
            event_queue.enqueue_event(create_task_status_event(
                context.task_id,
                create_task_status(TaskState.completed)
            ))
            logger.debug("Task completed successfully")

        except Exception as e:
            logger.error(f"Error in stream method: {str(e)}")
            event_queue.enqueue_event(create_task_status_event(
                context.task_id,
                create_task_status(TaskState.failed, str(e))
            ))
            raise

    @override
    async def cancel(self, context: RequestContext, event_queue: EventQueue) -> None:
        logger.debug("Cancelling task")
        event_queue.enqueue_event(create_task_status_event(
            context.task_id,
            create_task_status(TaskState.cancelled)
        ))

    async def start(self):
        logger.debug("Starting ClassifierAgent")
        return True

    async def stop(self):
        logger.debug("Stopping ClassifierAgent")
        return True

    @override
    async def execute(self, context: RequestContext, event_queue: EventQueue) -> None:
        try:
            # Log the full incoming message object
            logger.info(f"[CLASSIFIER] Full incoming message: {context.message!r}")

            # Log each part in message.parts
            for idx, part in enumerate(context.message.parts):
                logger.info(f"[CLASSIFIER] part[{idx}] type: {type(part)}, value: {part!r}")

            # Try to extract text (log what is actually extracted)
            message_text = ""
            for idx, part in enumerate(context.message.parts):
                extracted = None
                if isinstance(part, dict):
                    if part.get('kind') == 'text':
                        extracted = part.get('text', '')
                else:
                    kind = getattr(part, 'kind', None)
                    text = getattr(part, 'text', None)
                    if kind == 'text' and text is not None:
                        extracted = text
                    root = getattr(part, 'root', None)
                    if root:
                        kind = getattr(root, 'kind', None)
                        text = getattr(root, 'text', None)
                        if kind == 'text' and text is not None:
                            extracted = text
                logger.info(f"[CLASSIFIER] part[{idx}] extracted: {extracted!r}")
                if extracted:
                    message_text += extracted

            logger.info(f"[CLASSIFIER] Final message_text passed to LLM: {message_text!r}")

            # Update task status to working
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
            task.status = TaskStatus(
                state=TaskState.working,
                timestamp=datetime.now(UTC).isoformat()
            )
            await self.task_store.save(task)

            # Get LLM response
            response = await self.chain.arun(user_message=message_text)
            logger.info(f"[CLASSIFIER] LLM response: {response}")

            # Always wrap LLM response in a Message with a TextPart
            response_message = Message(
                messageId=str(uuid.uuid4()),
                role=Role.agent,
                parts=[TextPart(text=str(response))]
            )

            # Send completed event
            event_queue.enqueue_event(TaskStatusUpdateEvent(
                contextId=context.context_id,
                taskId=context.task_id,
                status=TaskStatus(
                    state=TaskState.completed,
                    message=response_message,
                    timestamp=datetime.now(UTC).isoformat()
                ),
                final=True
            ))

        except Exception as e:
            logger.error(f"Error in classifier execute: {str(e)}")
            error_message = Message(
                messageId=str(uuid.uuid4()),
                role=Role.agent,
                parts=[TextPart(text=f"An error occurred: {str(e)}")]
            )
            event_queue.enqueue_event(TaskStatusUpdateEvent(
                contextId=context.context_id,
                taskId=context.task_id,
                status=TaskStatus(
                    state=TaskState.failed,
                    message=error_message,
                    timestamp=datetime.now(UTC).isoformat()
                ),
                final=True
            ))