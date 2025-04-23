"""ShoppingAgent – LangChain JSON chat agent wired with search & wishlist tools"""
from langchain_community.llms import Ollama
from langchain.schema import SystemMessage
from langchain.tools import Tool
from langchain.agents import AgentExecutor, create_json_chat_agent
from langchain.memory import ConversationBufferMemory

from tools.search_tool import search_products
from tools.wishlist_tool import add_to_wishlist

# --- define tools -----------------------------------------------------------
search_tool = Tool(
    name="search_products",
    func=lambda q: search_products(q, k=5),
    description="Search the web for products that match a query."
)

wishlist_tool = Tool(
    name="add_to_wishlist",
    func=lambda data: add_to_wishlist(data["product"], data.get("alert_price")),
    description="Add a selected product (dict) to the user's wishlist with optional alert_price."
)

tools = [search_tool, wishlist_tool]

# --- LLM & memory -----------------------------------------------------------
# Use a locally‑served Llama 2 model via Ollama.
llm = Ollama(model="llama2", temperature=0)
memory = ConversationBufferMemory(memory_key="chat_history", return_messages=True)

system_msg = SystemMessage(
    content=(
        "You are ShoppingAssistant, a helpful agent that finds e‑commerce products, "
        "asks follow‑up questions, requires the user to pick exactly ONE product before "
        "adding it to their wishlist, and stores price‑alert thresholds. "
        "Always communicate in concise English. Use the available tools when needed."
    )
)

agent = create_json_chat_agent(llm, tools, system_message=system_msg)
agent_executor = AgentExecutor(agent=agent, tools=tools, verbose=True, memory=memory)


def get_agent_response(user_msg: str) -> str:
    """Run the agent and return its response string."""
    resp = agent_executor.invoke({"input": user_msg})
    return resp["output"]
