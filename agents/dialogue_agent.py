import streamlit as st
from langchain_groq import ChatGroq

GROQ_API_KEY = "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"

llm = ChatGroq(
    model_name="llama3-8b-8192",
    groq_api_key=GROQ_API_KEY
)

st.title("💬 GroqBot - Dialogue Agent")

if "history" not in st.session_state:
    st.session_state.history = []

user_input = st.chat_input("Say something!")

if user_input:
    st.session_state.history.append({"role": "user", "content": user_input})
    response = llm.invoke(user_input)
    st.session_state.history.append({"role": "ai", "content": response.content})

for chat in st.session_state.history:
    if chat["role"] == "user":
        st.markdown(f"**You:** {chat['content']}")
    else:
        st.markdown(f"**🤖 GroqBot:** {chat['content']}")


