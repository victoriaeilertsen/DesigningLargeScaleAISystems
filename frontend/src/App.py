import sys
import os
import uuid
import asyncio
from typing import Dict, List, Any
from dotenv import load_dotenv
import aiohttp
import logging
import json

# Fix the import path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

from agents.classifier.agent import ClassifierAgent
from agents.shopping.agent import ShoppingAgent
from agents.orchestrator.agent import OrchestratorAgent
from utils.a2a_utils import (
    log_a2a_message,
    create_message,
    get_a2a_message_send_payload,
    stream_agent_response
)
from a2a.types import Message
from a2a.server.tasks import InMemoryTaskStore

import streamlit as st

# Loading environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

A2A_SERVER_URL = os.getenv("A2A_SERVER_URL", "http://localhost:8000/a2a")

# Page configuration
st.set_page_config(
    page_title="Smart Shopping Assistant",
    page_icon="🛍️",
    layout="wide"
)

# Initialize task store
task_store = InMemoryTaskStore()

# Initialize session state
if "messages" not in st.session_state:
    st.session_state.messages = []
if "current_task_id" not in st.session_state:
    st.session_state.current_task_id = None
if "agents" not in st.session_state:
    st.session_state.agents = {
        "orchestrator": OrchestratorAgent(task_store),
        "classifier": ClassifierAgent(task_store),
        "shopping": ShoppingAgent(task_store)
    }
if "wishlist" not in st.session_state:
    st.session_state.wishlist = []
if "debug_mode" not in st.session_state:
    st.session_state.debug_mode = False
if "debug_log" not in st.session_state:
    st.session_state.debug_log = []

async def process_message(prompt: str, task_id: str) -> None:
    """Process user message with streaming A2A support.
    
    Args:
        prompt: User's input message
        task_id: Unique task ID
    """
    try:
        st.session_state.debug_log = st.session_state.get("debug_log", [])
        st.session_state.debug_log.append(f"[DEBUG] process_message called with prompt='{prompt}', task_id='{task_id}'")
        
        message = create_message(prompt, role="user", message_id=task_id)
        log_a2a_message(message, "outgoing")
        st.session_state.debug_log.append(f"[DEBUG] Created A2A message: {message.model_dump()}")

        response_text = ""
        response_placeholder = st.empty()
        debug_events = []
        event_count = 0

        # Add user message and empty assistant message to history
        st.session_state.messages.append({
            "sender": "user",
            "content": prompt,
            "task_id": task_id
        })
        assistant_msg = {
            "sender": "assistant",
            "content": "",
            "task_id": task_id,
            "debug": None
        }
        st.session_state.messages.append(assistant_msg)
        logger.info(f"[DEBUG] Added messages to history. Current messages count: {len(st.session_state.messages)}")

        async for event in stream_agent_response(prompt, A2A_SERVER_URL):
            event_count += 1
            debug_events.append(event)
            logger.info(f"[DEBUG] Processing event #{event_count}: {event.model_dump()}")
            st.session_state.debug_log.append(f"[DEBUG] Received event #{event_count}: {event.model_dump()}")
            
            if isinstance(event, TaskArtifactUpdateEvent):
                artifact = event.artifact
                logger.info(f"[DEBUG] Processing artifact: {artifact.model_dump()}")
                logger.info(f"[DEBUG] Artifact name: {artifact.name}")
                
                # Display text only from artifacts intended for the user
                allowed_names = ["orchestrator_response", "shopping_response", "classifier_response"]
                if artifact.name in allowed_names:
                    if artifact.parts and artifact.parts[0].root.text:
                        text = artifact.parts[0].root.text
                        logger.info(f"[DEBUG] Adding text to response: {text}")
                        response_text += text
                        response_placeholder.markdown(response_text)
                        st.session_state.messages[-1]["content"] = response_text
                        logger.info(f"[DEBUG] Updated assistant message content: {response_text}")
                elif st.session_state.debug_mode:
                    # In debug mode, show everything
                    if artifact.parts and artifact.parts[0].root.text:
                        text = f"[DEBUG: {artifact.name}] {artifact.parts[0].root.text}"
                        response_text += text
                        response_placeholder.markdown(response_text)
                        st.session_state.messages[-1]["content"] = response_text
                        logger.info(f"[DEBUG] Updated assistant message content (debug): {response_text}")
            
            elif isinstance(event, TaskStatusUpdateEvent):
                status = event.status
                logger.info(f"[DEBUG] Processing status update: {status.model_dump()}")
                # --- DIAGNOSTIC LOGS ---
                logger.info(f"[DEBUG] status.message: {getattr(status, 'message', None)}")
                if hasattr(status, 'message') and status.message and hasattr(status.message, 'parts'):
                    logger.info(f"[DEBUG] status.message.parts: {status.message.parts}")
                # --- END LOGS ---
                # Extract and display LLM response from status.message.parts
                if hasattr(status, 'message') and status.message and hasattr(status.message, 'parts') and status.message.parts:
                    part = status.message.parts[0]
                    text = None
                    print(f"[DEBUG] Processing part: {part}")
                    if isinstance(part, dict):
                        print(f"[DEBUG] Part is dict: {part}")
                        if part.get('kind') == 'text':
                            text = part.get('text', '')
                            print(f"[DEBUG] Extracted text from dict part: {text}")
                    else:
                        root = getattr(part, 'root', None)
                        print(f"[DEBUG] Part is object, root: {root}")
                        logger.info(f"[DEBUG] part.root: {root!r}")
                        if root:
                            kind = getattr(root, 'kind', None)
                            print(f"[DEBUG] Root kind: {kind}")
                            logger.info(f"[DEBUG] part.root.kind: {kind!r}")
                            logger.info(f"[DEBUG] part.root.text: {getattr(root, 'text', None)!r}")
                            if kind == 'text':
                                text = getattr(root, 'text', '')
                                print(f"[DEBUG] Extracted text from object part: {text}")
                                logger.info(f"[DEBUG] (FIX) Extracted text from status.message.parts: {text!r}")
                                response_text += text if text is not None else ''
                                print(f"[DEBUG] Updated response_text: {response_text}")
                                response_placeholder.markdown(response_text)
                                st.session_state.messages[-1]["content"] = response_text
                                print(f"[DEBUG] Updated message content: {st.session_state.messages[-1]}")
                                logger.info(f"[DEBUG] Updated assistant message content (status): {response_text}")
                            else:
                                logger.info(f"[DEBUG] (FIX) root.kind is not 'text', got: {kind!r}")
                    logger.info(f"[DEBUG] Extracted text from status.message.parts: {text!r}")
                    # Always display extracted text, even if it is an empty string.
                    # NOTE: In production, you may want to filter out empty responses or handle them differently.
                    response_text += text if text is not None else ''
                    response_placeholder.markdown(response_text)
                    st.session_state.messages[-1]["content"] = response_text
                    logger.info(f"[DEBUG] Updated assistant message content (status): {response_text}")
                if status.state in ["completed", "failed"]:
                    logger.info(f"[DEBUG] Task {status.state}")
                    break

        # After streaming, attach debug info to the assistant message
        st.session_state.messages[-1]["debug"] = debug_events
        logger.info(f"[DEBUG] Final assistant message: {json.dumps(st.session_state.messages[-1], indent=2)}")
        # Reset current_task_id after task completion
        st.session_state.current_task_id = None

        # Tuż przed wyświetleniem wiadomości w UI
        print("Final message state:", st.session_state.messages[-1])

    except Exception as e:
        logger.error(f"[DEBUG] Exception in process_message: {str(e)}", exc_info=True)
        st.session_state.debug_log.append(f"[ERROR] Exception in process_message: {str(e)}")
        st.error(f"An error occurred while processing the message: {str(e)}")

def main():
    st.title("🛍️ Smart Shopping Assistant")
    st.markdown('<span style="font-size:1.5em; font-weight:bold; background: linear-gradient(90deg, #ff8a00, #e52e71); -webkit-background-clip: text; -webkit-text-fill-color: transparent;">Your Personal Shopping Guide</span>', unsafe_allow_html=True)
    
    # Debug session states before message handling
    logger.info(f"[DEBUG] Before process_message: messages={len(st.session_state.messages)}, debug_log={len(st.session_state.debug_log)}")
    logger.info(f"[DEBUG] Messages content: {st.session_state.messages}")
    
    # Sidebar with agent information and wishlist
    with st.sidebar:
        # Wishlist section
        st.header("🎯 Wishlist")
        
        if st.session_state.wishlist:
            st.subheader("Your Wishlist Items:")
            for item in st.session_state.wishlist:
                with st.expander(item['name'], expanded=True):
                    col1, col2, col3 = st.columns([2, 1, 1])
                    with col1:
                        st.markdown(f"**Price:** {item['price']}")
                    with col2:
                        if st.button("🔗", key=f"link_{item['name']}"):
                            st.experimental_open_url(item['store_url'])
                    with col3:
                        if st.button("🗑️", key=f"delete_{item['name']}"):
                            st.session_state.wishlist.remove(item)
                            st.rerun()
        
        st.divider()
        
        # Debug mode toggle
        st.header("🛠️ Debugging")
        st.session_state.debug_mode = st.checkbox("Debug mode", value=st.session_state.debug_mode)
        
        # Debug log display
        if st.session_state.debug_mode and st.session_state.get("debug_log"):
            st.subheader("Debug Log:")
            for entry in st.session_state.debug_log[-30:]:
                st.markdown(f'<span style="color:gray; font-size: 0.8em;">{entry}</span>', unsafe_allow_html=True)
        
        # Expandable agents section
        st.header("🤖 Available Agents")
        for agent_name, agent in st.session_state.agents.items():
            with st.expander(f"{agent.agent_card.name} Agent", expanded=False):
                st.write(agent.agent_card.description)
                st.write("Capabilities:")
                for capability in agent.agent_card.capabilities:
                    st.write(f"- {capability}")

    # Display chat history
    for msg in st.session_state.messages:
        role = "user" if msg["sender"] == "user" else "assistant"
        with st.chat_message(role):
            st.write(msg["content"])
            if st.session_state.debug_mode and "debug" in msg and msg["debug"]:
                st.markdown(f'<span style="color:gray; font-size: 0.8em;">Debug: {msg["debug"]}</span>', unsafe_allow_html=True)

    # User input
    if prompt := st.chat_input("What are you looking for today?"):
        if not st.session_state.current_task_id:
            st.session_state.current_task_id = str(uuid.uuid4())
        asyncio.run(process_message(prompt, st.session_state.current_task_id))
        logger.info(f"[DEBUG] After process_message: messages={len(st.session_state.messages)}, debug_log={len(st.session_state.debug_log)}")
        logger.info(f"[DEBUG] Messages content after process_message: {st.session_state.messages}")
        st.rerun()

if __name__ == "__main__":
    main()
