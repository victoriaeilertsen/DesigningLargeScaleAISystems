import sys
import os
import uuid
import asyncio
from typing import Dict, List, Any
from dotenv import load_dotenv

# Fix the import path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

from agents.dialogue_agent import DialogueAgent
from agents.shopping_agent import ShoppingAgent
from utils.helpers import create_a2a_message, log_a2a_message

import streamlit as st

# Loading environment variables
load_dotenv()

# Page configuration
st.set_page_config(
    page_title="Smart Agent Chat",
    page_icon="🤖",
    layout="wide"
)

# Session state initialization
if "messages" not in st.session_state:
    st.session_state.messages = []
if "current_task_id" not in st.session_state:
    st.session_state.current_task_id = None
if "agents" not in st.session_state:
    st.session_state.agents = {
        "dialogue": DialogueAgent(),
        "shopping": ShoppingAgent()
    }
if "wishlist" not in st.session_state:
    st.session_state.wishlist = []
if "debug_mode" not in st.session_state:
    st.session_state.debug_mode = False

async def process_message(prompt: str, task_id: str) -> None:
    """Asynchronous message processing.
    
    Args:
        prompt: User message
        task_id: Task ID
    """
    try:
        # Create A2A message
        message = create_a2a_message(
            content=prompt,
            task_id=task_id
        )
        
        # Log message
        log_a2a_message(message, "outgoing")
        
        # Send message to dialogue agent
        response = await st.session_state.agents["dialogue"].handle_message(message, context={})
        
        # Log response
        log_a2a_message(response, "incoming")
        
        # Add message to history
        st.session_state.messages.append({
            "sender": "user",
            "content": prompt,
            "task_id": task_id
        })
        
        if response.get("type") == "text":
            st.session_state.messages.append({
                "sender": "assistant",
                "content": response["content"],
                "task_id": task_id,
                "debug": response
            })
            # If intent is search, call shopping agent
            if response.get("intent") == "search":
                shopping_response = await st.session_state.agents["shopping"].handle_message(message, context={})
                st.session_state.messages.append({
                    "sender": "shopping-agent",
                    "content": shopping_response["content"],
                    "task_id": task_id,
                    "debug": shopping_response
                })
        else:
            st.session_state.messages.append({
                "sender": "assistant",
                "content": f"An error occurred: {response.get('error', 'Unknown error')}",
                "task_id": task_id,
                "debug": response
            })
            
    except Exception as e:
        st.error(f"An error occurred while processing the message: {str(e)}")

def main():
    st.title("🤖 Smart Agent Chat ")
    st.markdown('<span style="font-size:1.5em; font-weight:bold; background: linear-gradient(90deg, #ff8a00, #e52e71); -webkit-background-clip: text; -webkit-text-fill-color: transparent;">(not so smart yet lol)</span>', unsafe_allow_html=True)
    
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
        role = "user" if msg["sender"] == "user" else ("assistant" if msg["sender"] == "assistant" else "shopping-agent")
        with st.chat_message(role):
            st.write(msg["content"])
            if st.session_state.debug_mode and "debug" in msg:
                st.markdown(f'<span style="color:gray; font-size: 0.8em;">Debug: {msg["debug"]}</span>', unsafe_allow_html=True)

    # User input
    if prompt := st.chat_input("Type your message..."):
        if not st.session_state.current_task_id:
            st.session_state.current_task_id = str(uuid.uuid4())
            
        # Run asynchronous message processing
        asyncio.run(process_message(prompt, st.session_state.current_task_id))
        st.rerun()

if __name__ == "__main__":
    main()
