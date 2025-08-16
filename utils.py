import os
from pypdf import PdfReader
import streamlit as st
import chromadb
from chromadb.config import Settings
from supabase import create_client, Client

# ---------------- Chroma Cloud Client ---------------- #
@st.cache_resource
def get_chroma_cloud_client():
    """
    Initialize a Chroma Cloud client using your tenant, database, and API key.
    """
    os.environ["CHROMA_API_KEY"] = st.secrets["CHROMA_API_KEY"]
    os.environ["CHROMA_TENANT"] = st.secrets["CHROMA_TENANT"]
    os.environ["CHROMA_DATABASE"] = st.secrets["CHROMA_DATABASE"]

    # Initialize Chroma client with REST API
    client = chromadb.Client(
        Settings(
            chroma_api_impl="rest",
        )
    )
    
    return client

# ---------------- Supabase Client ---------------- #
@st.cache_resource
def get_supabase_client() -> Client:
    """
    Initialize Supabase client once and reuse across session.
    """
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]
    return create_client(url, key)

# ---------------- PDF Processing ---------------- #
def process_pdf(file_path, progress_callback=None):
    reader = PdfReader(file_path)
    texts = []
    total = len(reader.pages)
    for i, page in enumerate(reader.pages):
        text = page.extract_text() or ""
        texts.append(text)
        if progress_callback:
            progress_callback((i + 1) / total)
    return texts

# ---------------- Vector DB Operations ---------------- #
def create_vector_database(texts, collection_name="pdf_collection"):
    """
    Create a collection in Chroma Cloud and add text documents.
    """
    chroma_client = get_chroma_cloud_client()

    try:
        chroma_client.delete_collection(name=collection_name)
    except Exception:
        pass

    collection = chroma_client.create_collection(name=collection_name)
    ids = [f"id{i+1}" for i in range(len(texts))]
    collection.add(documents=texts, ids=ids)

    return collection, chroma_client

# ---------------- Temporary Files ---------------- #
def delete_temp_files(file_path):
    if os.path.exists(file_path):
        os.remove(file_path)

# ---------------- Global Query Counter ---------------- #
def get_global_query_count() -> int:
    supabase = get_supabase_client()
    data = supabase.table("global_counter").select("count").eq("id", 1).execute()
    if data.data:
        return data.data[0]["count"]
    return 0

def increment_global_query_count():
    supabase = get_supabase_client()
    current = get_global_query_count()
    supabase.table("global_counter").update({"count": current + 1}).eq("id", 1).execute()
    return current + 1
