from langchain_ollama import OllamaLLM
from langchain.chains import ConversationChain
from langchain.memory import ConversationBufferMemory


llm = OllamaLLM(
    model="llama2", 
    temperature=0,
    system_prompt="""
        You are Nora, a helpful assistant whose job is to classify and summarize the user's need in JSON format.

        Step 1: Ask the user what they need. 
        Step 2: Ask follow-up questions to understand:
            - What the user wants
            - Any specific details (location, budget, preferences, time frame, etc.)
        Step 3: Once you feel confident you understand their need, output a JSON like:

        {
            "need": "Short weekend trip",
            "budget": "1000 NOK",
            "preferences": ["nature", "quiet"]
        }

        Important:
        - DO NOT explain the JSON. Just output it.
        - Once you output the JSON, stop asking more questions.
    """)

memory = ConversationBufferMemory()
conversation = ConversationChain(llm=llm, memory=memory, verbose=True)

while True:
    print("Hi! I help you figure out what you need. Tell me what you're looking for.")
    user_input = input("🧑 You: ").strip()
    if user_input.lower() in ["exit", "quit"]:
        print("👋 Bye!")
        break

    response = conversation.invoke({"input": user_input})
    reply = response['response']
    print(f"🤖 Nora: {reply}")



