import streamlit as st
import requests
import json
from datetime import datetime
import time

# --- PAGE CONFIG ---
st.set_page_config(
    page_title="Shopping Assistant",
    page_icon="🛍️",
    layout="wide"
)

# --- SESSION STATE ---
if "messages" not in st.session_state:
    st.session_state.messages = []
if "wishlist" not in st.session_state:
    st.session_state.wishlist = []

# --- CUSTOM CSS ---
st.markdown("""
<style>
.block-container { padding-top: 2rem !important; }
.agent-transition { font-size: 0.9rem; color: #8b9cb3; margin: 0.5rem 0; padding: 0.5rem; border-left: 3px solid #8b9cb3; background-color: rgba(139, 156, 179, 0.1); }
.wishlist-box { background: #232b3b; border-radius: 1rem; box-shadow: 0 2px 8px #0002; padding: 1.2rem 1.2rem 0.5rem 1.2rem; border: 1.5px solid #3a4252; min-height: 560px; max-height: 560px; display: flex; flex-direction: column; }
.wishlist-title-row { display: flex; align-items: center; justify-content: flex-end; margin-bottom: 0.2rem; margin-top: 0; }
.wishlist-title { font-size: 1.5rem; font-weight: 600; color: #fff; margin-right: 0.5rem; }
.wishlist-badge { display: inline-block; min-width: 32px; padding: 0.2em 0.7em; font-size: 1.1rem; font-weight: 700; color: #fff; background: linear-gradient(90deg, #6a8cff 0%, #b16cff 100%); border-radius: 1em; margin-left: 0.2em; box-shadow: 0 1px 4px #0002; }
.clear-btn-row { display: flex; justify-content: flex-end; align-items: center; margin-bottom: 0.5rem; margin-top: 0.5rem; }
.chat-header-row { display: flex; align-items: center; justify-content: space-between; margin-bottom: 0.5rem; margin-top: 0.5rem; }
</style>
""", unsafe_allow_html=True)

# --- LAYOUT ---
header_col1, header_col2 = st.columns([3, 1], gap="large")

with header_col1:
    st.markdown("""
    <div class='chat-header-row'>
        <div style='font-size:2.1rem;font-weight:700;color:#fff;display:inline-block;'>🛍️ Shopping Assistant</div>
        <span style='float:right;'>
            <form action="#" method="post" style="margin:0;display:inline;">
                <button type="submit" name="clear_chat" style="background: #232b3b; color: #fff; border: 1.5px solid #3a4252; border-radius: 0.7em; font-size: 1.1rem; font-weight: 500; padding: 0.5em 1.2em; cursor: pointer; transition: background 0.2s;">🗑️ Clear Chat History</button>
            </form>
        </span>
    </div>
    """, unsafe_allow_html=True)

with header_col2:
    st.markdown(f"""
    <div class='wishlist-title-row' style='justify-content:flex-end; margin-top:0.5rem; margin-bottom:0.5rem;'>
        <span class='wishlist-title' style='font-size:2.1rem;font-weight:700;color:#fff;margin-right:0.5rem;'>Wishlist</span>
        <span class='wishlist-badge'>{len(st.session_state.wishlist)}</span>
    </div>
    """, unsafe_allow_html=True)

main_col, wishlist_col = st.columns([3, 1], gap="large")

# --- CLEAR CHAT BUTTON HANDLER ---
if st.query_params.get("clear_chat") == "true":
    st.session_state.messages = []
    st.query_params.clear()

# --- CHAT PANEL ---
with main_col:
    chat_container = st.container(height=500)
    with chat_container:
        for idx, message in enumerate(st.session_state.messages):
            with st.chat_message(message["role"]):
                st.markdown(message["content"])
                if "route" in message:
                    st.markdown(f'<div class="agent-transition">🔄 Route: {message["route"]}</div>', unsafe_allow_html=True)
                if message["role"] == "assistant" and any(x in message["content"] for x in ["1.", "- ", "• "]):
                    lines = message["content"].split("\n")
                    for line in lines:
                        if line.strip().startswith("1."):
                            product = line.strip()[2:].strip()
                            if st.button(f"Add to wishlist: {product}", key=f"add_{idx}"):
                                if product not in st.session_state.wishlist:
                                    st.session_state.wishlist.append(product)
                                    st.success(f"Added '{product}' to wishlist!")
    prompt = st.chat_input("Type your message...")
    if prompt:
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.spinner("Processing..."):
            try:
                response = requests.post(
                    "http://localhost:8000/chat",
                    json={"content": prompt},
                    timeout=25
                )
                if response.status_code == 200:
                    data = response.json()
                    assistant_response = data["response"]
                    route = data.get("route", "?")
                    st.session_state.messages.append({
                        "role": "assistant",
                        "content": assistant_response,
                        "route": route
                    })
                else:
                    st.session_state.messages.append({
                        "role": "assistant",
                        "content": "Sorry, there was a problem processing your request.",
                        "route": "?"
                    })
            except Exception as e:
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": f"Sorry, an error occurred: {str(e)}",
                    "route": "?"
                })
        st.rerun()

# --- WISHLIST PANEL ---
with wishlist_col:
    st.markdown("<div class='wishlist-box'>", unsafe_allow_html=True)
    st.markdown("<div class='wishlist-scroll'>", unsafe_allow_html=True)
    if st.session_state.wishlist:
        for i, item in enumerate(st.session_state.wishlist):
            st.markdown(f"- {item}")
            if st.button(f"Remove", key=f"rem_{i}"):
                st.session_state.wishlist.pop(i)
                st.rerun()
    st.markdown("</div>", unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True) 