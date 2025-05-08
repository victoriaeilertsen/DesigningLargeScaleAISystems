import streamlit as st
from tools.search_tool import search_products
from typing import Dict, List, Optional
import json

class ShoppingAgent:
    def __init__(self):
        self.name = "Shopping"
        self.description = "Agent for product search and comparison"
        self.capabilities = ["shopping", "products", "prices", "stores", "search"]
        self.tasks = {}

    def get_agent_card(self) -> Dict:
        return {
            "name": self.name,
            "description": self.description,
            "capabilities": self.capabilities,
            "endpoint": "/api/agents/shopping"
        }

    def can_handle(self, message: str) -> bool:
        return any(capability.lower() in message.lower() for capability in self.capabilities)

    def process_message(self, message: str, task_id: str = None, messages: List = None) -> Dict:
        if task_id not in self.tasks:
            self.tasks[task_id] = {
                "status": "submitted",
                "messages": [],
                "context": {}
            }

        task = self.tasks[task_id]
        task["status"] = "working"
        task["messages"].append({"role": "user", "content": message})
        context = task["context"]

        # If message is a context JSON, update context
        try:
            incoming_context = json.loads(message)
            if isinstance(incoming_context, dict):
                context.update(incoming_context)
        except Exception:
            pass

        # Step 1: Generate product suggestions if not already done
        if "suggestions" not in context:
            query = f"{context.get('category', '')} {context.get('preferences', '')} budget {context.get('budget', '')}"
            results = search_products(query, 3)
            context["suggestions"] = results
            suggestion_lines = []
            for idx, product in enumerate(results, start=1):
                suggestion_lines.append(f"{idx}. {product['name']} - {product['features']} (link: {product['url']})")
            response = "Here are some options I found:\n" + "\n".join(suggestion_lines)
            response += "\nWhich one interests you most? Please reply with the number."
            task["messages"].append({"role": "agent", "content": response})
            task["status"] = "awaiting_selection"
            return {
                "task_id": task_id,
                "status": task["status"],
                "response": response
            }

        # Step 2: Wait for user to pick a product
        if "selected" not in context:
            # Try to parse user selection
            try:
                selection = int(message.strip())
                if 1 <= selection <= len(context["suggestions"]):
                    context["selected"] = context["suggestions"][selection-1]
                else:
                    raise ValueError
            except Exception:
                ask = f"Please reply with the number (1-{len(context['suggestions'])}) of the product you are interested in."
                task["messages"].append({"role": "agent", "content": ask})
                task["status"] = "awaiting_selection"
                return {
                    "task_id": task_id,
                    "status": task["status"],
                    "response": ask
                }
            # Confirm selection
            selected = context["selected"]
            confirm = f"Great choice! The current price for {selected['name']} is unknown (price tracking coming soon). What is the maximum price you would like to pay before I notify you?"
            task["messages"].append({"role": "agent", "content": confirm})
            task["status"] = "awaiting_alert_price"
            return {
                "task_id": task_id,
                "status": task["status"],
                "response": confirm
            }

        # Step 3: Wait for user to set price alert
        if "alert_price" not in context:
            # Try to parse price
            try:
                price = float(message.strip().replace(",", ".").replace("€", "").replace("PLN", "").strip())
                context["alert_price"] = price
            except Exception:
                ask = "Please enter the price (number only) at which you want to be notified."
                task["messages"].append({"role": "agent", "content": ask})
                task["status"] = "awaiting_alert_price"
                return {
                    "task_id": task_id,
                    "status": task["status"],
                    "response": ask
                }
            # Confirm addition to wishlist
            selected = context["selected"]
            confirm = f"Done! I have added {selected['name']} to your wishlist and will alert you when the price drops to {context['alert_price']} or lower."
            task["messages"].append({"role": "agent", "content": confirm})
            task["status"] = "completed"
            return {
                "task_id": task_id,
                "status": task["status"],
                "response": confirm
            }

        # If everything is done
        task["status"] = "completed"
        return {
            "task_id": task_id,
            "status": task["status"],
            "response": "Let me know if you need help with anything else!"
        }

def get_shopping_agent():
    return ShoppingAgent()

def shopping_agent():
    st.title("Shopping Agent")

    user_input = st.chat_input("What product do you want to search for?", key="shop_input")

    if user_input:
        with st.spinner("Searching for products..."):
            results = search_products("Buy"+ user_input, 4) 

        st.subheader(f"Search results for: **{user_input}**")
        for idx, product in enumerate(results, start=1):
            st.markdown(f"**{idx}. {product['name']} {product['url']}**  ")

