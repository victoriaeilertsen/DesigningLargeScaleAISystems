import streamlit as st
from langchain_groq import ChatGroq

# Groq API key
GROQ_API_KEY = "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"

llm = ChatGroq(
    model_name="llama3-8b-8192",
    groq_api_key=GROQ_API_KEY
)

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
