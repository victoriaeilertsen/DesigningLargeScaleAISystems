import sys
import os
import uuid
from typing import Dict, List

# Fix the import path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../agents')))
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../protocols')))

from dialogue_agent import get_dialogue_agent
from shopping_agent import get_shopping_agent
from a2a_handler import A2AHandler

import streamlit as st

# Page configuration
st.set_page_config(
    page_title="A2A Chat Interface",
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
        "dialogue": get_dialogue_agent(),
        "shopping": get_shopping_agent()
    }
if "wishlist" not in st.session_state:
    # Test item for demonstration
    st.session_state.wishlist = [{
        "name": "Mountain Bike Trek X-Caliber 8",
        "price": "€1,299.99",
        "store_url": "https://www.trekbikes.com"
    }]
if "a2a_handler" not in st.session_state:
    st.session_state.a2a_handler = A2AHandler({
        "dialogue": st.session_state.agents["dialogue"],
        "shopping": st.session_state.agents["shopping"]
    })

handler = st.session_state.a2a_handler

def main():
    st.title("🤖 A2A Chat Interface")
    
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
        
        # Expandable agents section
        st.header("🤖 Available Agents")
        for agent_name, agent in st.session_state.agents.items():
            with st.expander(f"{agent.name} Agent", expanded=False):
                st.write(agent.description)
                st.write("Capabilities:")
                for capability in agent.capabilities:
                    st.write(f"- {capability}")

    # Display chat history for the current task (only once, always full history)
    if st.session_state.current_task_id:
        task = handler.get_task(st.session_state.current_task_id)
        st.write(f"DEBUG: Number of messages in task: {len(task.messages) if task else 'No task'}")
        if task:
            for msg in task.messages:
                sender = msg["sender"] if isinstance(msg, dict) else msg.sender
                content = msg["content"] if isinstance(msg, dict) else msg.content
                role = "user" if sender == "user" else "assistant"
                with st.chat_message(role):
                    st.write(content)

    # User input
    if prompt := st.chat_input("Type your message..."):
        if not st.session_state.current_task_id:
            st.session_state.current_task_id = str(uuid.uuid4())
        handler.submit_task(
            sender="user",
            receiver="dialogue",
            content=prompt,
            task_id=st.session_state.current_task_id
        )
        st.rerun()

if __name__ == "__main__":
    main()
