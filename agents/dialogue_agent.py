import streamlit as st
from langchain_groq import ChatGroq
from typing import Dict, List, Optional
import json
import os
from schemas.a2a_message import A2AMessage


# Load example dialog from file (as system prompt)
EXAMPLE_DIALOG_PATH = os.path.join(os.path.dirname(__file__), '../docs/example_dialog.md')
if os.path.exists(EXAMPLE_DIALOG_PATH):
    with open(EXAMPLE_DIALOG_PATH, "r", encoding="utf-8") as f:
        EXAMPLE_DIALOG = f.read()
else:
    EXAMPLE_DIALOG = ""  # fallback if file not found

DIALOGUE_AGENT_SYSTEM_PROMPT = f"""
You are a helpful shopping assistant. Your job is to help the user find exactly what they are looking for, regardless of product type. Always clarify the user's needs, budget, and preferences. If you are unsure, ask follow-up questions. When you have all the information, summarize and say you will search for the best options.

Below is an example conversation for inspiration (do not copy, just use as a guide):

{EXAMPLE_DIALOG}
"""

class DialogueAgent:
    def __init__(self):
        import streamlit as st
        import os
        
        if "GROQ_API_KEY" in st.secrets:
            api_key = st.secrets["GROQ_API_KEY"]
        else:
            from dotenv import load_dotenv
            load_dotenv()
            api_key = os.getenv("GROQ_API_KEY")
        

        if api_key is None:
            raise ValueError("GROQ_API_KEY is not set in secrets or .env file")

        self.llm = ChatGroq(
            model_name="llama3-8b-8192",
            api_key=api_key
        )
        self.name = "Dialogue"
        self.description = (
            "Agent for need clarification and conversation. "
            "Your job is to help the user define what they want, their budget, and preferences, "
            "then forward the task to the shopping agent."
        )
        self.capabilities = ["conversation", "clarification", "help", "information"]
        self.tasks = {}

    def get_agent_card(self) -> Dict:
        return {
            "name": self.name,
            "description": self.description,
            "capabilities": self.capabilities,
            "endpoint": "/api/agents/dialogue"
        }

    def can_handle(self, message: str) -> bool:
        return True  # Always handle, as this is the entry agent

    def process_message(self, message: str, task_id: str = None, messages: List = None) -> Dict:
        # Use provided messages (full history) for context
        if task_id not in self.tasks:
            self.tasks[task_id] = {
                "status": "active",
                "context": {}
            }
        task = self.tasks[task_id]
        context = task["context"]
        if messages is None:
            return {
                "task_id": task_id,
                "status": "error",
                "response": "No message history provided."
            }

        # Build conversation history for LLM
        history = ""
        for m in messages:
            prefix = "User:" if m.sender == "user" else "Agent:"
            history += f"{prefix} {m.content}\n"

        # Extraction prompts (always update context, never overwrite existing info)
        if "category" not in context:
            extract_category = self.llm.invoke(
                f"Based on the conversation so far, what is the product or category the user is looking for? Reply with only the product/category or 'unknown'.\nConversation:\n{history}"
            ).content.strip().lower()
            if extract_category != "unknown":
                context["category"] = extract_category
        if "budget" not in context:
            extract_budget = self.llm.invoke(
                f"Based on the conversation so far, what is the user's budget? Reply with only the budget (e.g. '100 USD', '400 PLN') or 'unknown'.\nConversation:\n{history}"
            ).content.strip().lower()
            if extract_budget != "unknown":
                context["budget"] = extract_budget
        if "preferences" not in context:
            extract_preferences = self.llm.invoke(
                f"Based on the conversation so far, what are the user's brand or feature preferences? Reply with only the preferences or 'unknown'.\nConversation:\n{history}"
            ).content.strip().lower()
            if extract_preferences != "unknown":
                context["preferences"] = extract_preferences

        # Ask only for missing info, always include current context in prompt
        if "category" not in context:
            ask = self.llm.invoke(
                f"The user has already provided: {json.dumps(context)}. Ask the user what product or category they are looking for. Be concise.\nConversation:\n{history}"
            ).content.strip()
            messages.append(A2AMessage(sender="dialogue", receiver="user", content=ask))
            return {
                "task_id": task_id,
                "status": "active",
                "response": ask
            }
        if "budget" not in context:
            ask = self.llm.invoke(
                f"The user has already provided: {json.dumps(context)}. Ask the user for their budget for a {context['category']}. Be concise.\nConversation:\n{history}"
            ).content.strip()
            messages.append(A2AMessage(sender="dialogue", receiver="user", content=ask))
            return {
                "task_id": task_id,
                "status": "active",
                "response": ask
            }
        if "preferences" not in context:
            ask = self.llm.invoke(
                f"The user has already provided: {json.dumps(context)}. Ask the user if they have any brand or feature preferences for a {context['category']}, or if you should focus on best price-to-quality. Be concise.\nConversation:\n{history}"
            ).content.strip()
            messages.append(A2AMessage(sender="dialogue", receiver="user", content=ask))
            return {
                "task_id": task_id,
                "status": "active",
                "response": ask
            }

        # If all info is present, summarize and forward
        summary = self.llm.invoke(
            f"The user has already provided: {json.dumps(context)}. Summarize the user's needs and say you will now search for the best {context['category']} options for them.\nConversation:\n{history}"
        ).content.strip()
        messages.append(A2AMessage(sender="dialogue", receiver="user", content=summary))
        context["history"] = [
            {"sender": m.sender, "receiver": m.receiver, "content": m.content, "timestamp": m.timestamp}
            for m in messages
        ]
        return {
            "task_id": task_id,
            "status": "forward",
            "response": summary,
            "forward_to": "shopping",
            "forward_content": json.dumps(context)
        }

def get_dialogue_agent():
    return DialogueAgent()

def need_classifier():
    st.title("Need Classifier Agent")

    if "full_need" not in st.session_state:
        st.session_state.full_need = None  
    if "history" not in st.session_state:
        st.session_state.history = []

    user_input = st.chat_input("Describe what you are looking for...")

    if user_input:
        st.session_state.history.append({"role": "user", "content": user_input})
        
        if st.session_state.full_need is None:
            prompt = f"""
                You are a Need Classifier Agent for products...
                User Input: "{user_input}"
                """
        else:
            prompt = f"""
                You are an assistant refining a previously classified user need...
                """

        response = llm.invoke(prompt)

        st.session_state.history.append({"role": "agent", "content": response.content})
        
        if "Classified Need:" in response.content:
            st.session_state.full_need = response.content

    for chat in st.session_state.history:
        if chat["role"] == "user":
            st.markdown(f"**You:** {chat['content']}")
        else:
            st.markdown(f"**🤖 Need Classifier:** {chat['content']}")

    if st.session_state.full_need:
        st.divider()
        st.header("📝 Final Classified Need")
        st.markdown(st.session_state.full_need)
