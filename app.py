import streamlit as st
import requests
import json
from datetime import datetime
import time
import re

# --- PAGE CONFIG ---
st.set_page_config(
    page_title="Shopping Assistant",
    page_icon="🛍️",
    layout="wide"
)

# --- Obsługa czyszczenia czatu przez parametr URL ---
if 'clear_chat' in st.query_params:
    st.session_state.messages = []
    # Usuwam parametr, by nie zapętlić
    st.query_params.clear()
    st.rerun()

def extract_products_and_advice_from_message(message):
    # Wyciąga produkty w formacie markdown oraz sekcję Advice
    # Nowy wzorzec: - **Product Name**  \n  Price: ...  \n  [Buy here](...)  \n  Description: ...
    product_pattern = r"- \*\*(.*?)\*\*\s+Price: ([^\n]+)\s+\[Buy here\]\(([^\)]+)\)\s+Description: ([^\n]+)"
    advice_pattern = r"Advice:(.*)"
    products = []
    for match in re.finditer(product_pattern, message, re.DOTALL):
        name = match.group(1).strip()
        price = match.group(2).strip()
        url = match.group(3).strip()
        description = match.group(4).strip()
        products.append({"name": name, "price": price, "url": url, "description": description})
    advice_match = re.search(advice_pattern, message, re.DOTALL)
    advice = advice_match.group(1).strip() if advice_match else ""
    return products, advice

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
.chat-message-container, .wishlist-box {
    background: #232b3b;
    border-radius: 1rem;
    box-shadow: 0 2px 8px #0002;
    padding: 1.2rem;
    border: 1.5px solid #3a4252;
    min-height: 560px;
    max-height: 560px;
    overflow-y: auto;
    display: flex;
    flex-direction: column;
}
.wishlist-title-row { display: flex; align-items: center; justify-content: space-between; margin-bottom: 1rem; }
.wishlist-title { font-size:2.1rem; font-weight:700; color:#fff; }
.wishlist-badge { display: inline-block; min-width: 32px; padding: 0.2em 0.7em; font-size: 1.1rem; font-weight: 700; color: #fff; background: linear-gradient(90deg, #6a8cff 0%, #b16cff 100%); border-radius: 1em; margin-left: 0.5rem; box-shadow: 0 1px 4px #0002; }
.product-card { background: #232b3b; border-radius: 0.8rem; padding: 1rem; margin-bottom: 1rem; border: 1px solid #3a4252; }
.product-title { font-size: 1.1rem; font-weight: 600; color: #fff; margin-bottom: 0.5rem; }
.product-price { font-size: 0.95rem; color: #b0b0b0; margin-bottom: 0.5rem; }
.product-description { font-size: 0.95em; color: #fff; margin-top: 0.2rem; }
.product-actions { display: flex; gap: 0.3rem; align-items: center; }
.icon-button { background: none; border: none; color: #8b9cb3; font-size: 1.2rem; cursor: pointer; padding: 0.2rem; }
.icon-button:hover { color: #fff; }
.wishlist-item { background: #232b3b; border-radius: 0.8rem; padding: 1rem; margin-bottom: 1rem; border: 1px solid #3a4252; }
.wishlist-item-title { font-size: 1.1rem; font-weight: 600; color: #fff; margin-bottom: 0.5rem; }
.wishlist-item-price { font-size: 0.95rem; color: #b0b0b0; margin-bottom: 0.5rem; }
.wishlist-item-actions { display: flex; gap: 0.5rem; }
.product-row { display: flex; gap: 0.3rem; align-items: center; margin-bottom: 0.1rem; }
</style>
""", unsafe_allow_html=True)

# --- LAYOUT ---
header_col1, header_col2 = st.columns([3, 1], gap="large")

with header_col1:
    st.markdown("""
    <div class='wishlist-title-row'>
        <div style='font-size:2.1rem;font-weight:700;color:#fff;display:inline-block;'>🛍️ Shopping Assistant</div>
        <button class='icon-button' onclick='clearChat()'>🗑️</button>
    </div>
    """, unsafe_allow_html=True)

with header_col2:
    st.markdown(f"""
    <div class='wishlist-title-row'>
        <span class='wishlist-title'>Wishlist</span>
        <span class='wishlist-badge'>{len(st.session_state.wishlist)}</span>
    </div>
    """, unsafe_allow_html=True)

main_col, wishlist_col = st.columns([3, 1], gap="large")

# --- CHAT PANEL ---
with main_col:
    chat_container = st.container(height=500)
    with chat_container:
        for idx, message in enumerate(st.session_state.messages):
            with st.chat_message(message["role"]):
                if message["role"] == "assistant" and "Shopping Agent" in message.get("route", ""):
                    products, advice = extract_products_and_advice_from_message(message["content"])
                    # Najpierw wyciągamy wstęp (resztę treści)
                    content_wo_products = re.sub(r"- \*\*.*?\*\*\s+Price: [^\n]+\s+\[Buy here\]\([^\)]+\)\s+Description: [^\n]+", "", message["content"], flags=re.DOTALL)
                    content_wo_products = re.sub(r"Advice:.*", "", content_wo_products, flags=re.DOTALL)
                    if content_wo_products.strip():
                        st.markdown(content_wo_products.strip())
                    # Potem produkty
                    for i, product in enumerate(products):
                        with st.container():
                            col1, col2, col3, col4 = st.columns([1.5, 0.5, 0.5, 0.5], gap="small")
                            with col1:
                                st.markdown(f"**{product['name']}**")
                            with col2:
                                st.markdown(f"{product['price']}")
                            with col3:
                                st.markdown(f'''<a href="{product['url']}" target="_blank" style="text-decoration:none;"><button style="background:#232b3b;border:1px solid #3a4252;border-radius:0.4em;padding:0.2em 0.7em;color:#8b9cb3;font-size:1.1rem;cursor:pointer;">🔗</button></a>''', unsafe_allow_html=True)
                            with col4:
                                if st.button("➕", key=f"add_{idx}_{i}"):
                                    if not any((p["name"] == product["name"] and p["url"] == product["url"]) for p in st.session_state.wishlist):
                                        st.session_state.wishlist.append(product)
                                        st.rerun()
                            if product.get("description"):
                                st.markdown(f"<div class='product-description'>{product['description']}</div>", unsafe_allow_html=True)
                            st.markdown("---")  # Separator między produktami
                    # Potem porada
                    if advice:
                        st.info(advice)
                else:
                    st.markdown(message["content"])
                if "route" in message:
                    st.markdown(f'<div class="agent-transition">🔄 Route: {message["route"]}</div>', unsafe_allow_html=True)

    prompt = st.chat_input("Type your message...")
    if prompt:
        st.session_state.messages.append({"role": "user", "content": prompt})
        with chat_container:
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
    wishlist_container = st.container(height=560)  # 500px chatbox + 60px input
    with wishlist_container:
        if st.session_state.wishlist:
            for i, item in enumerate(st.session_state.wishlist):
                # Nazwa na górze
                st.markdown(f"**{item['name']}**")
                # Pod spodem: cena, link, usuń w jednej linii
                col1, col2, col3 = st.columns([1, 0.7, 0.7], gap="small")
                with col1:
                    st.markdown(f"{item['price']}")
                with col2:
                    st.markdown(f'''<a href="{item['url']}" target="_blank" style="text-decoration:none;"><button style="background:#232b3b;border:1px solid #3a4252;border-radius:0.4em;padding:0.2em 0.7em;color:#8b9cb3;font-size:1.1rem;cursor:pointer;">🔗</button></a>''', unsafe_allow_html=True)
                with col3:
                    if st.button("🗑️", key=f"rem_{i}"):
                        st.session_state.wishlist.pop(i)
                        st.rerun()
                st.markdown("---")  # Separator między produktami

# --- JavaScript for handling button clicks ---
st.markdown("""
<script>
function clearChat() {
    const url = new URL(window.location.href);
    url.searchParams.set('clear_chat', '1');
    window.location.href = url.toString();
}

function addToWishlist(index) {
    // Implementacja dodawania do wishlisty
}

function removeFromWishlist(index) {
    // Implementacja usuwania z wishlisty
}
</script>
""", unsafe_allow_html=True) 