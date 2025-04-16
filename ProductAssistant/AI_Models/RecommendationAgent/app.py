from langchain_ollama import OllamaLLM
from langchain_community.tools import DuckDuckGoSearchRun
from langchain.agents import initialize_agent, Tool
from langchain.agents import AgentType 


llm = OllamaLLM(
    model="llama2",
    temperature=0,
    system_prompt="""
            You are an AI assistant whose ONLY job is to use tools to answer user questions.

            IMPORTANT RULES:
            - You MUST always use the tools.
            - DO NOT answer directly unless the answer comes from a tool.
            - DO NOT make up answers or summaries.
            - As soon as the tool returns an answer, use it and STOP.

            Format your reasoning like this:
            Thought: [what you're thinking]
            Action: [tool name]
            Action Input: [what to search]

            Once you receive the tool output and have an answer:
            Final Answer: [the actual answer, copied or summarized from tool output]

            ❌ Never write anything outside of this format.
            ❌ Never describe your process.
            ❌ Never continue after Final Answer.

            ---

            💡 Example:

            User: Where can I buy a Dyson V15?

            Thought: I should search for where to buy the Dyson V15.
            Action: DuckDuckGo Search
            Action Input: Dyson V15 buy

            [Tool runs and returns search results]

            Final Answer: You can buy the Dyson V15 at dyson.com and Best Buy: https://www.bestbuy.com/site/dyson-v15

            ---

            Now begin.
            """

        )

search=DuckDuckGoSearchRun()
tools=[
    Tool(
        name="DuckDuckGo Search",
        func= search.run,
        description ="Useful for when you need to answer questions about current events. You should ask targeted questions"
    )
]

agent = initialize_agent(
    tools, 
    llm, 
    agent=AgentType.ZERO_SHOT_REACT_DESCRIPTION, 
    verbose=True,
    handle_parsing_errors=True
)

try: 
    response= agent.run("What is the current price of Asics Novablast 5?")
    print(response)
except Exception as e:
    print(f"An error occured {e}")
