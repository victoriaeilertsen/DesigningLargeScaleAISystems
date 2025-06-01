import streamlit as st
import requests
import json
from datetime import datetime

# Page configuration
st.set_page_config(
    page_title="Shopping Assistant",
    page_icon="🛍️",
    layout="wide"
)

# CSS styles
st.markdown("""
<style>
    .main {
        padding: 2rem;
    }
    .stTextInput>div>div>input {
        font-size: 1.1rem;
    }
    .chat-message {
        padding: 1.5rem;
        border-radius: 0.5rem;
        margin-bottom: 1rem;
        display: flex;
        flex-direction: column;
    }
    .chat-message.user {
        background-color: #2b313e;
    }
    .chat-message.assistant {
        background-color: #475063;
    }
    .chat-message .content {
        display: flex;
        margin-top: 0.5rem;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state
if "messages" not in st.session_state:
    st.session_state.messages = []

# Header
st.title("🛍️ Shopping Assistant")

# Chat container
chat_container = st.container()

# Display message history
with chat_container:
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

# Message input
if prompt := st.chat_input("Type your message..."):
    # Add user message to history
    st.session_state.messages.append({"role": "user", "content": prompt})
    
    # Display user message
    with st.chat_message("user"):
        st.markdown(prompt)
    
    # Display assistant message (placeholder)
    with st.chat_message("assistant"):
        message_placeholder = st.empty()
        message_placeholder.markdown("⌛ Processing...")
        
        try:
            # Send request to API
            response = requests.post(
                "http://localhost:8000/chat",
                json={"content": prompt},
                timeout=30
            )
            
            if response.status_code == 200:
                assistant_response = response.json()["response"]
                message_placeholder.markdown(assistant_response)
                st.session_state.messages.append({"role": "assistant", "content": assistant_response})
            else:
                message_placeholder.markdown("❌ Error communicating with the assistant.")
        except Exception as e:
            message_placeholder.markdown(f"❌ Error: {str(e)}")

# Clear history button
if st.button("🗑️ Clear History"):
    st.session_state.messages = []
    st.rerun() 