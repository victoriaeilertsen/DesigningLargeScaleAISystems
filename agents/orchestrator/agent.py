from a2a.types import AgentCard, AgentCapabilities, AgentSkill, TaskStatus, TaskState, TaskArtifactUpdateEvent, Artifact, Part, TextPart, TaskStatusUpdateEvent, Message
from a2a.server.agent_execution import AgentExecutor, RequestContext
from a2a.server.events import EventQueue
from typing_extensions import override
import re
import asyncio
import aiohttp
import os
import logging
import uuid
import json

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

from utils.a2a_utils import (
    create_task_status,
    create_message,
    create_streaming_message,
    create_task_status_event,
    create_artifact,
    create_artifact_part_text
)
from utils.errors import ValidationError, TaskNotFoundError
from .prompts import ORCHESTRATOR_SYSTEM_PROMPT

# --- LANGCHAIN IMPORTS ---
from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain
from langchain_google_genai import ChatGoogleGenerativeAI

class OrchestratorAgent(AgentExecutor):
    def __init__(self):
        logger.debug("Initializing OrchestratorAgent")
        
        self.agent_card = AgentCard(
            name="orchestrator-agent",
            description="Agent responsible for coordinating and routing requests to specialized agents.",
            version="0.1.0",
            url="http://localhost:8000",
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
        self.system_prompt = ORCHESTRATOR_SYSTEM_PROMPT
        self.agent_endpoints = {
            "classifier": "http://localhost:8001/stream",
            "shopping": "http://localhost:8002/stream"
        }
        
        # --- LANGCHAIN SETUP ---
        logger.debug("Setting up LangChain components")
        self.prompt = PromptTemplate(
            input_variables=["user_message", "target_agent"],
            template=ORCHESTRATOR_SYSTEM_PROMPT
        )
        api_key = os.getenv("GOOGLE_API_KEY")
        if not api_key:
            raise ValueError("GOOGLE_API_KEY environment variable not set")
        self.llm = ChatGoogleGenerativeAI(
            api_key=api_key,
            model="gemini-1.5-flash"
        )
        self.chain = LLMChain(llm=self.llm, prompt=self.prompt)
        logger.debug("LangChain setup completed")
        super().__init__()

    def _determine_target_agent(self, message: str) -> str:
        """Determine which agent should handle the request."""
        # Check for shopping-related keywords
        if re.search(r"(kupi|znajd|szukaj|zamów|order|buy|find|product|price|cost)", message, re.IGNORECASE):
            return "shopping"
        # Default to classifier agent for general conversation
        return "classifier"

    @override
    async def execute(self, context: RequestContext, event_queue: EventQueue) -> None:
        logger.info("=== [ORCH EXECUTE CALLED] ===")
        try:
            logger.debug("Starting execute method")
            
            # Validate input
            if not context.message.parts:
                logger.error("No message parts found")
                raise ValidationError("Message must contain at least one part")

            # Update task status to running
            logger.debug("Enqueueing task status: working")
            try:
                event_queue.enqueue_event(TaskStatusUpdateEvent(
                    contextId=context.context_id,
                    taskId=context.task_id,
                    status=TaskStatus(state=TaskState.working),
                    final=False
                ))
            except Exception as e:
                logger.error(f"Enqueue failed (working): {type(e).__name__}: {e}")
                raise

            # Get message
            user_message = context.message.parts[0].root.text
            logger.debug(f"Processing message: {user_message}")

            # Determine target agent
            target_agent = self._determine_target_agent(user_message)
            logger.debug(f"Target agent determined: {target_agent}")

            # Create artifact with routing decision
            artifact = Artifact(
                artifactId=str(uuid.uuid4()),
                name="routing_decision",
                parts=[Part(root=TextPart(
                    kind='text',
                    metadata=None,
                    text=json.dumps({
                    "message": user_message,
                    "target_agent": target_agent,
                    "reason": f"Message contains keywords indicating {target_agent} agent should handle it"
                    })
                ))]
            )
            logger.debug("Enqueueing task artifact: routing_decision")
            try:
                event = TaskArtifactUpdateEvent(
                    contextId=context.context_id,
                    taskId=context.task_id,
                    artifact=artifact
                )
                event_queue.enqueue_event(event)
            except Exception as e:
                logger.error(f"Enqueue failed (artifact): {type(e).__name__}: {e}")
                raise

            # --- LANGCHAIN EXECUTION ---
            logger.debug("Starting LLM execution")
            try:
                response = await asyncio.get_event_loop().run_in_executor(
                    None, 
                    lambda: self.chain.invoke({
                        "user_message": user_message,
                        "target_agent": target_agent
                    })
                )
                logger.debug(f"LLM response received: {response}")
                # Extract text for A2A protocol compliance
                if isinstance(response, dict) and "text" in response:
                    response_text = response["text"]
                else:
                    response_text = str(response)
                logger.debug("Enqueueing streaming message")
                try:
                    artifact = Artifact(
                        artifactId=str(uuid.uuid4()),
                        name="orchestrator_response",
                        parts=[Part(root=TextPart(
                            kind='text',
                            metadata=None,
                            text=response_text
                        ))]
                    )
                    event = TaskArtifactUpdateEvent(
                        contextId=context.context_id,
                        taskId=context.task_id,
                        artifact=artifact
                    )
                    event_queue.enqueue_event(event)
                except Exception as e:
                    logger.error(f"Enqueue failed (streaming): {type(e).__name__}: {e}")
                    raise
            except Exception as e:
                logger.error(f"Error in LLM execution: {str(e)}")
                raise

            # Update task status to completed
            logger.debug("Enqueueing task status: completed")
            try:
                event_queue.enqueue_event(TaskStatusUpdateEvent(
                    contextId=context.context_id,
                    taskId=context.task_id,
                    status=TaskStatus(state=TaskState.completed),
                    final=True
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
                error_message = Message(
                    messageId=str(uuid.uuid4()),
                    role="agent",
                    parts=[Part(root=TextPart(kind="text", text=str(e)))]
                )
                event_queue.enqueue_event(TaskStatusUpdateEvent(
                    contextId=context.context_id,
                    taskId=context.task_id,
                    status=TaskStatus(state=TaskState.failed, message=error_message),
                    final=True
                ))
            except Exception as e2:
                logger.error(f"Enqueue failed (failed): {type(e2).__name__}: {e2}")
                raise
            raise

    @override
    async def stream(self, context: RequestContext, event_queue: EventQueue) -> None:
        logger.info("=== [ORCH STREAM CALLED] ===")
        try:
            logger.info(f"[FORWARDING] TaskID: {context.task_id}, ContextID: {context.context_id}")
            logger.info("[FORWARDING] Enqueueing task status: working")
            event_queue.enqueue_event(create_task_status_event(
                context.task_id,
                create_task_status(TaskState.working)
            ))

            user_message = context.message.parts[0].root.text
            logger.info(f"[FORWARDING] Processing message (stream): {user_message}")

            target_agent = self._determine_target_agent(user_message)
            logger.info(f"[FORWARDING] Target agent determined: {target_agent}")

            # Enqueue routing_decision artifact
            routing_decision = {
                "message": user_message,
                "target_agent": target_agent,
                "reason": f"Message contains keywords indicating {target_agent} agent should handle it"
            }
            event_queue.enqueue_event(TaskArtifactUpdateEvent(
                contextId=context.context_id,
                taskId=context.task_id,
                artifact=Artifact(
                    artifactId=str(uuid.uuid4()),
                    name="routing_decision",
                    parts=[Part(root=TextPart(
                        kind='text',
                        metadata=None,
                        text=json.dumps(routing_decision)
                    ))]
                )
            ))

            # Forward to target agent
            target_url = self.agent_endpoints[target_agent]
            logger.info(f"[FORWARDING] Sending to {target_agent} at {target_url}")
            logger.info(f"[FORWARDING] POST to {target_url}")
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    target_url,
                    json={
                        "jsonrpc": "2.0",
                        "id": str(uuid.uuid4()),
                        "method": "message/stream",
                        "params": {
                            "message": {
                                "role": "user",
                                "parts": [{"kind": "text", "text": user_message}],
                                "messageId": str(uuid.uuid4())
                            }
                        }
                    }
                ) as response:
                    logger.info(f"[FORWARDING] HTTP status: {response.status}")
                    async for line in response.content:
                        if line:
                            try:
                                line_text = line.decode("utf-8")
                                logger.info(f"[FORWARDING] Received line: {line_text}")
                                if line_text.startswith("data: "):
                                    event_data = json.loads(line_text[6:])
                                    if "result" in event_data:
                                        result = event_data["result"]
                                        if "artifact" in result:
                                            event_queue.enqueue_event(TaskArtifactUpdateEvent(
                                                contextId=context.context_id,
                                                taskId=context.task_id,
                                                artifact=result["artifact"]
                                            ))
                                        elif "status" in result:
                                            event_queue.enqueue_event(TaskStatusUpdateEvent(
                                                contextId=context.context_id,
                                                taskId=context.task_id,
                                                status=result["status"],
                                                final=result.get("final", False)
                                            ))
                            except Exception as e:
                                logger.error(f"Error processing event from {target_agent}: {str(e)}")
                                continue

            # Mark task as completed
            event_queue.enqueue_event(create_task_status_event(
                context.task_id,
                create_task_status(TaskState.completed),
                final=True
            ))

        except Exception as e:
            logger.error(f"Error in stream method: {str(e)}")
            event_queue.enqueue_event(create_task_status_event(
                context.task_id,
                create_task_status(TaskState.failed, str(e)),
                final=True
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