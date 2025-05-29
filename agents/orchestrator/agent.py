from a2a.types import AgentCard, AgentCapabilities, AgentSkill, TaskStatus, TaskState, TaskArtifactUpdateEvent, Artifact, Part, TextPart, TaskStatusUpdateEvent, Message, Role, Task
from a2a.server.agent_execution import AgentExecutor, RequestContext
from a2a.server.events import EventQueue
from typing_extensions import override
from typing import Optional, AsyncGenerator
import re
import asyncio
import aiohttp
import os
import logging
import uuid
import json
from config.settings import AGENT_CONFIG, TASK_CONFIG
from loguru import logger
from datetime import datetime, UTC

from utils.a2a_utils import (
    create_task_status,
    create_message,
    create_streaming_message,
    create_task_status_event,
    create_artifact,
    create_artifact_part_text,
    get_a2a_message_send_payload
)
from utils.errors import ValidationError, TaskNotFoundError, AgentCommunicationError
from .prompts import ORCHESTRATOR_SYSTEM_PROMPT

# --- LANGCHAIN IMPORTS ---
from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain
from langchain_google_genai import ChatGoogleGenerativeAI

from a2a.server.events.event_queue import EventQueue
from a2a.server.tasks import InMemoryTaskStore

class OrchestratorAgent(AgentExecutor):
    def __init__(self, task_store: InMemoryTaskStore):
        logger.debug("=== [ORCHESTRATOR] Initializing OrchestratorAgent ===")
        
        self.agent_card = AgentCard(
            name=AGENT_CONFIG["orchestrator"]["name"],
            description=AGENT_CONFIG["orchestrator"]["description"],
            version="0.1.0",
            url=AGENT_CONFIG["orchestrator"]["url"],
            documentationUrl="https://example.com/orchestrator-agent/docs",
            capabilities=AgentCapabilities(
                streaming=True,
                pushNotifications=True,
                stateTransitionHistory=True
            ),
            defaultInputModes=["text/plain", "application/json"],
            defaultOutputModes=["text/plain", "application/json"],
            skills=[
                AgentSkill(
                    id="orchestration",
                    name="Request Orchestration",
                    description="Routes requests to appropriate specialized agents.",
                    tags=["orchestration", "routing", "coordination"],
                    examples=[
                        "I want to buy a laptop",
                        "Hello, how are you?",
                        "What's the weather like?"
                    ],
                    inputModes=["text/plain", "application/json"],
                    outputModes=["text/plain", "application/json"]
                )
            ]
        )
        logger.debug(f"[ORCHESTRATOR] Agent card created: {self.agent_card.model_dump()}")
        
        self.system_prompt = ORCHESTRATOR_SYSTEM_PROMPT
        self.agent_endpoints = {
            "classifier": f"{AGENT_CONFIG['classifier']['url']}/a2a",
            "shopping": f"{AGENT_CONFIG['shopping']['url']}/a2a"
        }
        logger.debug(f"[ORCHESTRATOR] Agent endpoints configured: {self.agent_endpoints}")
        
        # --- LANGCHAIN SETUP ---
        logger.debug("[ORCHESTRATOR] Setting up LangChain components")
        self.prompt = PromptTemplate(
            input_variables=["user_message", "target_agent"],
            template=ORCHESTRATOR_SYSTEM_PROMPT
        )
        api_key = os.getenv("GOOGLE_API_KEY")
        if not api_key:
            logger.error("[ORCHESTRATOR] GOOGLE_API_KEY not set in environment variables")
            raise ValueError("GOOGLE_API_KEY environment variable not set")
        self.llm = ChatGoogleGenerativeAI(
            api_key=api_key,
            model="gemini-1.5-flash"
        )
        self.chain = LLMChain(llm=self.llm, prompt=self.prompt)
        logger.debug("[ORCHESTRATOR] LangChain setup completed")
        self.task_store = task_store
        super().__init__()

    async def _determine_target_agent(self, message_text: str) -> Optional[str]:
        """Determine which agent should handle the message."""
        try:
            # Use LLM to determine target agent
            response = await self.llm.ainvoke(
                f"""Analyze the following message and determine which agent should handle it.
                Available agents: shopping, classifier
                Return only the agent name.
                
                Message: {message_text}"""
            )
            text = response.content if hasattr(response, 'content') else str(response)
            logger.info(f"LLM response for agent determination: {text}")
            if "shopping" in text.lower():
                return "shopping"
            elif "classifier" in text.lower():
                return "classifier"
            return None
        except Exception as e:
            logger.error(f"Error determining target agent: {str(e)}")
            return None

    async def _forward_to_agent(self, target_agent: str, context: RequestContext) -> AsyncGenerator[TaskStatusUpdateEvent, None]:
        """Forward the message to the target agent."""
        try:
            if target_agent not in self.agent_endpoints:
                raise ValueError(f"Unknown agent: {target_agent}")
            
            # Create HTTP client session
            async with aiohttp.ClientSession() as session:
                # Prepare payload
                payload = get_a2a_message_send_payload(context.message)
                
                # Send request to target agent
                async with session.post(self.agent_endpoints[target_agent], json=payload) as response:
                    if response.status != 200:
                        raise AgentCommunicationError(f"Failed to communicate with {target_agent}: {response.status}")
            
                    # Process response stream
                    async for line in response.content:
                        if line:
                            try:
                                event_data = json.loads(line.decode('utf-8'))
                                if 'data' in event_data:
                                    event = TaskStatusUpdateEvent.model_validate_json(event_data['data'])
                                    yield event
                            except json.JSONDecodeError as e:
                                logger.error(f"Error decoding event: {str(e)}")
                                continue
                
        except Exception as e:
            logger.error(f"Error forwarding to agent {target_agent}: {str(e)}")
            error_message = Message(
                messageId=str(uuid.uuid4()),
                role=Role.agent,
                parts=[TextPart(text=f"Error forwarding to {target_agent}: {str(e)}")]
            )
            yield TaskStatusUpdateEvent(
                contextId=context.context_id,
                taskId=context.task_id,
                status=TaskStatus(
                    state=TaskState.failed,
                    message=error_message,
                    timestamp=datetime.now(UTC).isoformat()
                ),
                final=True
            )

    @override
    async def execute(self, context: RequestContext, event_queue: EventQueue) -> None:
        try:
            message_text = ""
            for part in context.message.parts:
                if isinstance(part, TextPart):
                    message_text += part.text
                elif isinstance(part, dict) and part.get('kind') == 'text':
                    message_text += part.get('text', '')
            
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
            
            target_agent = await self._determine_target_agent(message_text)
            if not target_agent:
                error_message = Message(
                    messageId=str(uuid.uuid4()),
                    role=Role.agent,
                    parts=[TextPart(text="I couldn't determine which agent should handle your request. Please try rephrasing.")]
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
                return
            
            async for event in self._forward_to_agent(target_agent, context):
                event_queue.enqueue_event(event)
                
        except Exception as e:
            logger.error(f"Error in orchestrator execute: {str(e)}")
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

    @override
    async def stream(self, context: RequestContext, event_queue: EventQueue) -> None:
        """Handle streaming requests."""
        logger.debug("[ORCHESTRATOR] Stream method called")
        try:
            if not context.context_id or not context.task_id:
                raise ValueError("Invalid context: missing context_id or task_id")
            
            async for event in self.execute(context):
                try:
                    event_queue.enqueue_event(event)
                except Exception as e:
                    logger.error(f"Error enqueueing event: {str(e)}")
                    raise
        except Exception as e:
            logger.error(f"Error in stream: {str(e)}")
            error_message = Message(
                messageId=str(uuid.uuid4()),
                role=Role.agent,
                parts=[TextPart(text=f"Error: {str(e)}")]
            )
            try:
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
            except Exception as e2:
                logger.error(f"Error sending error event: {str(e2)}")

    @override
    async def cancel(self, context: RequestContext, event_queue: EventQueue) -> None:
        """Handle task cancellation."""
        logger.info(f"[ORCHESTRATOR] Cancelling task {context.task_id}")
        try:
            # Get task
            task = await self.task_store.get(context.task_id)
            if task:
                # Update task status
                task.status = TaskStatus(
                    state=TaskState.canceled,
                    timestamp=datetime.now(UTC).isoformat()
                )
                await self.task_store.save(task)
            
            # Send cancellation event
            event_queue.enqueue_event(TaskStatusUpdateEvent(
                contextId=context.context_id,
                taskId=context.task_id,
                status=TaskStatus(
                    state=TaskState.canceled,
                    timestamp=datetime.now(UTC).isoformat()
                ),
                final=True
            ))
            logger.debug("[ORCHESTRATOR] Successfully enqueued cancellation status")
        except Exception as e:
            logger.error(f"[ORCHESTRATOR] Error in cancel: {str(e)}")
            error_message = Message(
                messageId=str(uuid.uuid4()),
                role=Role.agent,
                parts=[TextPart(text=f"Error cancelling task: {str(e)}")]
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

    async def start(self):
        """Start the orchestrator agent."""
        logger.info("=== [ORCHESTRATOR] Starting OrchestratorAgent ===")
        # Add any startup logic here

    async def stop(self):
        """Stop the orchestrator agent."""
        logger.info("=== [ORCHESTRATOR] Stopping OrchestratorAgent ===")
        # Add any cleanup logic here 