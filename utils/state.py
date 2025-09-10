# utils/state.py
import streamlit as st

def reset_session_state():
    st.session_state.products = []
    st.session_state.user_query = ""
