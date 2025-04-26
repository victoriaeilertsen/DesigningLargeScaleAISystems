import streamlit as st
from langchain_groq import ChatGroq

# Groq API key
GROQ_API_KEY = "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"

# Groq LLM
llm = ChatGroq(
    model_name="llama3-8b-8192",
    groq_api_key=GROQ_API_KEY
)

st.title("Need Classifier")

# Initialize session state
if "full_need" not in st.session_state:
    st.session_state.full_need = None  
if "history" not in st.session_state:
    st.session_state.history = []

# User input
user_input = st.chat_input("Describe what you are looking for...")

if user_input:
    st.session_state.history.append({"role": "user", "content": user_input})
    
    # FIRST input → create need from scratch
    if st.session_state.full_need is None:
        prompt = f"""
            You are a Need Classifier Agent for products.

            Analyze the user's input, elaborate it smartly (terrain, waterproofing, materials, etc.), and identify missing information.

            Format:
            Classified Need: <full description>
            Inferred Details: <assumptions you made>
            Missing Information: <what is missing?>
            Follow-up Question: <question if needed>

            User Input: "{user_input}"
            """
    else:
        # SUBSEQUENT inputs → refine the previous need
        prompt = f"""
            You are an assistant refining a previously classified user need.

            Previous Need:
            {st.session_state.full_need}

            New User Input:
            "{user_input}"

            Task:
            - Update the Classified Need with the new information.
            - Remove contradictions if any.
            - Keep it detailed and actionable.
            - List any still Missing Information and ask ONE follow-up question if needed.

            Respond using the same format:
            Classified Need: <updated description>
            Inferred Details: <any assumptions>
            Missing Information: <still missing?>
            Follow-up Question: <next question, or "None">
            """

    # Get model response
    response = llm.invoke(prompt)
    
    # Save agent response
    st.session_state.history.append({"role": "agent", "content": response.content})
    
    # Update full need (always replace with newest one)
    if "Classified Need:" in response.content:
        st.session_state.full_need = response.content

# Display the conversation
for chat in st.session_state.history:
    if chat["role"] == "user":
        st.markdown(f"**You:** {chat['content']}")
    else:
        st.markdown(f"**🤖 Need Classifier:** {chat['content']}")

# Display final classified need
if st.session_state.full_need:
    st.divider()
    st.header("📝 Final Classified Need (Live Updated)")
    st.markdown(st.session_state.full_need)
