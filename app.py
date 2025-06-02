import streamlit as st
import requests
import json
from datetime import datetime
import time

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
    .processing-status {
        display: flex;
        align-items: center;
        gap: 0.5rem;
        color: #8b9cb3;
        font-style: italic;
        margin-top: 0.5rem;
    }
    .agent-info {
        font-size: 0.8rem;
        color: #8b9cb3;
        margin-top: 0.5rem;
    }
    @keyframes spin {
        0% { transform: rotate(0deg); }
        100% { transform: rotate(360deg); }
    }
    .spinner {
        display: inline-block;
        width: 1rem;
        height: 1rem;
        border: 2px solid #8b9cb3;
        border-radius: 50%;
        border-top-color: transparent;
        animation: spin 1s linear infinite;
    }
    .agent-transition {
        font-size: 0.9rem;
        color: #8b9cb3;
        margin: 0.5rem 0;
        padding: 0.5rem;
        border-left: 3px solid #8b9cb3;
        background-color: rgba(139, 156, 179, 0.1);
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
            if "route" in message:
                st.markdown(f'<div class="agent-transition">🔄 Route: {message["route"]}</div>', unsafe_allow_html=True)

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
        status_placeholder = st.empty()
        
        # Show initial processing status
        status_placeholder.markdown(
            '<div class="processing-status"><div class="spinner"></div> 🤔 Orchestrator Agent is analyzing your request...</div>',
            unsafe_allow_html=True
        )
        
        try:
            # Send request to API with increased timeout
            response = requests.post(
                "http://localhost:8000/chat",
                json={"content": prompt},
                timeout=25
            )
            
            if response.status_code == 200:
                data = response.json()
                assistant_response = data["response"]
                agent_info = data.get("agent_info", "Shopping Agent")
                route = data.get("route", "Orchestrator → Shopping Agent")
                
                # Update status based on agent
                if "classifier" in agent_info.lower():
                    status_placeholder.markdown(
                        '<div class="processing-status"><div class="spinner"></div> 🔍 Classifier Agent is analyzing your requirements...</div>',
                        unsafe_allow_html=True
                    )
                elif "shopping" in agent_info.lower():
                    status_placeholder.markdown(
                        '<div class="processing-status"><div class="spinner"></div> 🛍️ Shopping Agent is searching for products...</div>',
                        unsafe_allow_html=True
                    )
                
                # Display response
                message_placeholder.markdown(assistant_response)
                # Display route immediately under the response
                st.markdown(f'<div class="agent-transition">🔄 Route: {route}</div>', unsafe_allow_html=True)
                
                # Update final status
                status_placeholder.markdown("")
                
                # Add to history with route only
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": assistant_response,
                    "route": route
                })
            else:
                status_placeholder.markdown(
                    '<div class="processing-status">❌ Error communicating with the assistant</div>',
                    unsafe_allow_html=True
                )
                message_placeholder.markdown("Sorry, there was a problem processing your request.")
        except requests.exceptions.Timeout:
            status_placeholder.markdown(
                '<div class="processing-status">⏳ The request is taking longer than expected. Please wait...</div>',
                unsafe_allow_html=True
            )
            message_placeholder.markdown("The system is still processing your request. Please wait a moment.")
        except Exception as e:
            status_placeholder.markdown(
                '<div class="processing-status">❌ An error occurred</div>',
                unsafe_allow_html=True
            )
            message_placeholder.markdown(f"Sorry, an error occurred: {str(e)}")

# Clear history button
if st.button("🗑️ Clear History"):
    st.session_state.messages = []
    st.rerun() 