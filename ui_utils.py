import streamlit as st

def inject_chat_css():
    pass  # No custom CSS needed for default UI

def display_chat_history(chat_history):
    for role, msg in chat_history:
        if role == "user":
            st.chat_message("user").write(msg)
        else:
            st.chat_message("assistant").write(msg)