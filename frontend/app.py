import streamlit as st
import asyncio
import json
from a2a.types import TaskStatusUpdateEvent, TaskArtifactUpdateEvent
import a2a_utils
import uuid

print("=== [DEBUG] app.py LOADED ===", flush=True)

def main():
    st.title("A2A Chat Interface")
    st.write("Welcome to the A2A chat interface!")
    
    # Initialize chat history
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []
    
    # Display chat history
    for message in st.session_state.chat_history:
        if message["user"]:
            st.write(f"User: {message['user']}")
        if message["assistant"]:
            st.write(f"Assistant: {message['assistant']}")
    
    # Chat input
    user_input = st.text_input("Type your message:", key="user_input")
    if st.button("Send"):
        if user_input:
            asyncio.run(process_message(user_input))
            st.session_state.user_input = ""

async def process_message(user_input: str):
    print("=== [DEBUG] process_message CALLED ===", flush=True)
    message_id = str(uuid.uuid4())
    st.session_state.messages.append({
        "sender": "user",
        "content": user_input,
        "task_id": message_id
    })
    assistant_message = {
        "sender": "assistant",
        "content": "",
        "task_id": message_id,
        "debug": []
    }
    st.session_state.messages.append(assistant_message)
    try:
        async for event in stream_agent_response(user_input):
            print("=== [DEBUG] stream_agent_response YIELD ===", flush=True)
            print(f"[DEBUG] Received event: {event}")
            if hasattr(event, 'artifact') and hasattr(event.artifact, 'name') and event.artifact.name == "orchestrator_response":
                for part in event.artifact.parts:
                    if hasattr(part, 'kind') and part.kind == "text":
                        assistant_message["content"] = part.text
                        st.session_state.messages[-1] = assistant_message
                        print(f"[DEBUG] Updated assistant message: {assistant_message}")
                        st.experimental_rerun()
            elif hasattr(event, 'status') and hasattr(event.status, 'state') and event.status.state == "completed":
                print(f"[DEBUG] Task completed: {event.task_id}")
    except Exception as e:
        print(f"[ERROR] Error processing message: {e}")
        assistant_message["content"] = f"Error: {str(e)}"
        st.session_state.messages[-1] = assistant_message
        st.experimental_rerun()

async def stream_agent_response(user_input: str):
    """Stream agent response and update chat history."""
    print(f"[DEBUG] Starting stream_agent_response for input: {user_input}")
    
    # Create a placeholder for the assistant's message
    st.session_state.chat_history.append({"user": user_input, "assistant": ""})
    
    # Stream the response
    async for event in a2a_utils.stream_agent_response(user_input):
        print(f"[DEBUG] Received event type: {type(event).__name__}")
        
        if isinstance(event, TaskStatusUpdateEvent):
            print(f"[DEBUG] Processing status update: {event.status}")
            # Update status in the last message
            st.session_state.chat_history[-1]["status"] = event.status
            st.rerun()
            
        elif isinstance(event, TaskArtifactUpdateEvent):
            print(f"[DEBUG] Processing artifact update: {event.artifact}")
            # Update the assistant's message in the last chat entry
            if event.artifact and "parts" in event.artifact and len(event.artifact["parts"]) > 0:
                try:
                    # Try to parse the text as JSON first (for routing_decision)
                    text = event.artifact["parts"][0]["text"]
                    try:
                        json_data = json.loads(text)
                        if "text" in json_data:
                            assistant_message = json_data["text"]
                        else:
                            assistant_message = text
                    except json.JSONDecodeError:
                        assistant_message = text
                        
                    print(f"[DEBUG] Updating assistant message to: {assistant_message}")
                    st.session_state.chat_history[-1]["assistant"] = assistant_message
                    st.rerun()
                except Exception as e:
                    print(f"[ERROR] Failed to process artifact: {e}")
                    print(f"[DEBUG] Artifact content: {event.artifact}")
            else:
                print("[ERROR] Invalid artifact structure received")
                print(f"[DEBUG] Artifact content: {event.artifact}")

if __name__ == "__main__":
    main() 