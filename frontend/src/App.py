import sys
import os

# Fix the import path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../agents')))

from dialogue_agent import need_classifier
from shopping_agent import shopping_agent

import streamlit as st


import streamlit as st

st.set_page_config(layout="wide")

col1, col2 = st.columns(2)

with col1:
    need_classifier()

with col2:
    shopping_agent()
