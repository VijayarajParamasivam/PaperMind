import sys
import pysqlite3
sys.modules["sqlite3"] = pysqlite3 

import streamlit as st
import os
import shutil
import chromadb
from chromadb.config import Settings

import google.generativeai as genai

from utils import process_pdf, delete_temp_files, get_global_query_count, increment_global_query_count, get_chroma_cloud_client
from chat_utils import build_context_chunks, build_history_text, build_prompt
from ui_utils import inject_chat_css, display_chat_history



def process_and_store(uploaded_file, api_key):
    try:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-1.5-flash')
    except Exception:
        st.error("Invalid Gemini API Key. Please check your key. Restarting...") 
        handle_invalid_api_key()

    temp_dir = "./temp"
    if not os.path.exists(temp_dir):
        os.makedirs(temp_dir)

    pdf_path = os.path.join(temp_dir, uploaded_file.name)
    with open(pdf_path, "wb") as f:
        f.write(uploaded_file.getbuffer())

    from pypdf import PdfReader
    reader = PdfReader(pdf_path)
    total_pages = len(reader.pages)

    # --- Use Chroma Cloud instead of in-memory local client ---
    chroma_client = get_chroma_cloud_client()

    # Delete existing collection if present
    try:
        chroma_client.delete_collection(name="pdf_collection")
    except Exception:
        pass
    collection = chroma_client.create_collection(name="pdf_collection")

    progress_bar = st.progress(0, text="Processing PDF and creating vector DB...")
    texts, ids = [], []

    for i, page in enumerate(reader.pages):
        text = page.extract_text() or ""
        texts.append(text)
        ids.append(f"id{i+1}")
        percent = int(((i + 1) / total_pages) * 100)
        progress_bar.progress(percent, text=f"Processing PDF... {percent}%")

    progress_bar.progress(100, text="Creating vector db...")
    collection.add(documents=texts, ids=ids)
    progress_bar.empty()

    return model, collection, pdf_path, chroma_client


def handle_invalid_api_key():
    st.error("Invalid Gemini API Key. Please enter a valid key and upload a PDF again.")
    
    for key in ["processed", "processing", "api_key", "uploaded_file",
                "model", "collection", "pdf_path", "chroma_client", "chat_history"]:
        if key in st.session_state:
            del st.session_state[key]

    st.info("Restarting...")
    import time
    time.sleep(3)
    st.rerun()


def main():
    st.title("PaperMind")
    st.caption("AI-powered PDF assistant")
    st.info(f"Doubts cleared so far : **{get_global_query_count()}**")

    inject_chat_css()

    if "processed" not in st.session_state:
        st.session_state.processed = False
    if "processing" not in st.session_state:
        st.session_state.processing = False

    if st.session_state.processing:
        st.markdown("<style>.block-container {padding-top: 10vh;}</style>", unsafe_allow_html=True)
        st.info("Please wait while your PDF is being processed...")

    if not st.session_state.processed:
        if not st.session_state.processing:
            api_key = st.text_input("Enter your Gemini API Key:")
            st.markdown(
                'Don\'t have an API key? Get it from [https://aistudio.google.com/apikey](https://aistudio.google.com/apikey)',
                unsafe_allow_html=True
            )
            uploaded_file = st.file_uploader("Upload a PDF file:", type=["pdf"])
            if st.button("Process PDF"):
                if api_key and uploaded_file:
                    st.session_state.api_key = api_key
                    st.session_state.uploaded_file = uploaded_file
                    st.session_state.processing = True
                    st.rerun()
                else:
                    st.error("Please provide both API key and PDF file.")

        if st.session_state.processing and not st.session_state.processed:
            try:
                model, collection, pdf_path, chroma_client = process_and_store(
                    st.session_state.uploaded_file, st.session_state.api_key
                )
            except Exception:
                st.session_state.processing = False
                st.error("Failed to process PDF. Restarting...")  
                handle_invalid_api_key()

            st.session_state.processed = True
            st.session_state.model = model
            st.session_state.collection = collection
            st.session_state.pdf_path = pdf_path
            st.session_state.chroma_client = chroma_client
            st.session_state.processing = False
            st.success("PDF processed and vector database created. Start chatting below!")
            st.rerun()

    else:
        st.success("PDF processed! Start chatting below.")
        if "chat_history" not in st.session_state:
            st.session_state.chat_history = []
        st.markdown(
            """
            <style>
            .block-container { padding-bottom: 80px !important; }
            @media (min-width: 768px) { .stChat { margin-bottom: 20px !important; } }
            </style>
            """,
            unsafe_allow_html=True
        )
        user_input = st.chat_input("Ask a question...")
        if user_input:
            collection = st.session_state.collection
            model = st.session_state.model

            try:
                results = collection.query(query_texts=[user_input], n_results=3)
                context_chunks = build_context_chunks(results)
                history = st.session_state.chat_history[-6:]
                history_text = build_history_text(history)
                prompt = build_prompt(context_chunks, history_text, user_input)

                gemini_response = model.generate_content(prompt)
                response = gemini_response.text.strip() or "Sorry, I couldn't find an answer in the PDF."
            except Exception:
                response = "Failed to generate response. Invalid API Key or API error."
                handle_invalid_api_key()

            increment_global_query_count()

            st.session_state.chat_history.append(("user", user_input))
            st.session_state.chat_history.append(("bot", response))

        display_chat_history(st.session_state.chat_history)

        if st.button("Clear Data"):
            clear()


def clear():
    delete_temp_files(st.session_state.pdf_path)
    try:
        st.session_state.chroma_client.delete_collection(name="pdf_collection")
    except Exception:
        pass
    if os.path.exists("./temp"):
        shutil.rmtree("./temp")
    for key in [
        "processed", "processing", "api_key", "uploaded_file",
        "model", "collection", "pdf_path", "chroma_client", "chat_history"
    ]:
        if key in st.session_state:
            del st.session_state[key]
    st.success("Data cleared. You can upload a new PDF.")
    st.rerun()


if __name__ == "__main__":
    main()
