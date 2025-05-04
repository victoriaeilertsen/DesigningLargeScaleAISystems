import streamlit as st
from tools.search_tool import search_products

def shopping_agent():
    st.title("Shopping Agent")

    user_input = st.chat_input("What product do you want to search for?", key="shop_input")

    if user_input:
        with st.spinner("Searching for products..."):
            results = search_products("Buy"+ user_input, 4) 

        st.subheader(f"Search results for: **{user_input}**")
        for idx, product in enumerate(results, start=1):
            st.markdown(f"**{idx}. {product['name']} {product['url']}**  ")

