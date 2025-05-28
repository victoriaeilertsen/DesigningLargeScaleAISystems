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
from utils.a2a_utils import log_a2a_message, create_message, get_a2a_message_send_payload
from a2a.types import Message

import streamlit as st

# Loading environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

A2A_SERVER_URL = os.getenv("A2A_SERVER_URL", "http://localhost:8000")

# Page configuration
st.set_page_config(
    page_title="Smart Shopping Assistant",
    page_icon="🛍️",
    layout="wide"
)

# Session state initialization
if "messages" not in st.session_state:
    st.session_state.messages = []
if "current_task_id" not in st.session_state:
    st.session_state.current_task_id = None
if "agents" not in st.session_state:
    st.session_state.agents = {
        "orchestrator": OrchestratorAgent(),
        "classifier": ClassifierAgent(),
        "shopping": ShoppingAgent()
    }
if "wishlist" not in st.session_state:
    st.session_state.wishlist = []
if "debug_mode" not in st.session_state:
    st.session_state.debug_mode = False
if "debug_log" not in st.session_state:
    st.session_state.debug_log = []

async def send_message_streaming_to_a2a_server(message: Message):
    payload = get_a2a_message_send_payload(message, method="message/stream")
    logger.info(f"[DEBUG] Sending message to A2A server (endpoint: /) with payload: {json.dumps(payload, indent=2)}")
    async with aiohttp.ClientSession() as session:
        async with session.post(f"{A2A_SERVER_URL}/", json=payload) as resp:
            logger.info(f"[DEBUG] Got response from A2A server (endpoint: /) with status: {resp.status}")
            async for line in resp.content:
                if line:
                    try:
                        line_text = line.decode("utf-8")
                        logger.info(f"[DEBUG] Raw SSE line: {line_text}")
                        if line_text.startswith("data: "):
                            json_str = line_text[6:].strip()
                            if json_str:
                                logger.info(f"[DEBUG] Parsing JSON from SSE: {json_str}")
                                event = json.loads(json_str)
                                logger.info(f"[DEBUG] Successfully parsed event: {json.dumps(event, indent=2)}")
                                yield event
                            else:
                                logger.warning("[DEBUG] Empty JSON string after 'data: ' prefix")
                        else:
                            logger.warning(f"[DEBUG] Line doesn't start with 'data: ': {line_text}")
                    except json.JSONDecodeError as e:
                        logger.error(f"[DEBUG] JSON parsing error: {e}")
                        logger.error(f"[DEBUG] Raw line that caused error: {line_text}")
                    except Exception as e:
                        logger.error(f"[DEBUG] Unexpected error: {e}")
                        logger.error(f"[DEBUG] Raw line that caused error: {line_text}")

async def process_message(prompt: str, task_id: str) -> None:
    """Asynchronous message processing with streaming A2A support."""
    try:
        st.session_state.debug_log = st.session_state.get("debug_log", [])
        st.session_state.debug_log.append(f"[DEBUG] process_message (streaming) called with prompt='{prompt}', task_id='{task_id}'")
        message = create_message(prompt, role="user", message_id=task_id)
        msg_dict = get_a2a_message_send_payload(message, method="message/stream")["params"]["message"]
        st.session_state.debug_log.append(f"[DEBUG] Created A2A message: {msg_dict}")
        log_a2a_message(message, "outgoing")
        st.session_state.debug_log.append(f"[DEBUG] Sent message to A2A server: {msg_dict}")

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

        async for event in send_message_streaming_to_a2a_server(message):
            event_count += 1
            debug_events.append(event)
            logger.info(f"[DEBUG] Processing event #{event_count}: {json.dumps(event, indent=2)}")
            st.session_state.debug_log.append(f"[DEBUG] Received event #{event_count}: {event}")
            
            if "result" in event:
                result = event["result"]
                logger.info(f"[DEBUG] Processing result: {json.dumps(result, indent=2)}")
                
                if result.get("kind") == "artifact-update":
                    artifact = result.get("artifact", {})
                    logger.info(f"[DEBUG] Processing artifact: {json.dumps(artifact, indent=2)}")
                    logger.info(f"[DEBUG] Artifact name: {artifact.get('name')}")
                    # Wyświetl tekst tylko z artifactów przeznaczonych dla usera
                    allowed_names = ["orchestrator_response", "shopping_response", "classifier_response"]
                    if artifact.get("name") in allowed_names:
                        if artifact.get("parts") and artifact["parts"][0].get("text"):
                            text = artifact["parts"][0]["text"]
                            logger.info(f"[DEBUG] Adding text to response: {text}")
                            response_text += text
                            response_placeholder.markdown(response_text)
                            st.session_state.messages[-1]["content"] = response_text
                            logger.info(f"[DEBUG] Updated assistant message content: {response_text}")
                    elif st.session_state.debug_mode:
                        # W trybie debug pokaż wszystko
                        if artifact.get("parts") and artifact["parts"][0].get("text"):
                            text = f"[DEBUG: {artifact.get('name')}] {artifact['parts'][0]['text']}"
                            response_text += text
                            response_placeholder.markdown(response_text)
                            st.session_state.messages[-1]["content"] = response_text
                            logger.info(f"[DEBUG] Updated assistant message content (debug): {response_text}")
                elif result.get("kind") == "status-update":
                    status = result.get("status", {})
                    logger.info(f"[DEBUG] Processing status update: {json.dumps(status, indent=2)}")
                    if status.get("state") in ["completed", "failed"]:
                        logger.info(f"[DEBUG] Task {status.get('state')}")
                        break
            else:
                logger.warning(f"[DEBUG] Event without result field: {json.dumps(event, indent=2)}")

        # After streaming, attach debug info to the assistant message
        st.session_state.messages[-1]["debug"] = debug_events
        logger.info(f"[DEBUG] Final assistant message: {json.dumps(st.session_state.messages[-1], indent=2)}")
        # Reset current_task_id po zakończeniu taska
        st.session_state.current_task_id = None

    except Exception as e:
        logger.error(f"[DEBUG] Exception in process_message: {str(e)}", exc_info=True)
        st.session_state.debug_log.append(f"[ERROR] Exception in process_message (streaming): {str(e)}")
        st.error(f"An error occurred while processing the message: {str(e)}")

def main():
    st.title("🛍️ Smart Shopping Assistant")
    st.markdown('<span style="font-size:1.5em; font-weight:bold; background: linear-gradient(90deg, #ff8a00, #e52e71); -webkit-background-clip: text; -webkit-text-fill-color: transparent;">Your Personal Shopping Guide</span>', unsafe_allow_html=True)
    
    # Debug stanów sesji przed obsługą wiadomości
    logger.info(f"[DEBUG] Before process_message: messages={len(st.session_state.messages)}, debug_log={len(st.session_state.debug_log)}")
    logger.info(f"[DEBUG] Zawartość messages: {st.session_state.messages}")
    
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
        logger.info(f"[DEBUG] Zawartość messages po process_message: {st.session_state.messages}")
        st.rerun()

if __name__ == "__main__":
    main()
