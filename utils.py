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
    client = chromadb.Client()
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
# Get the current global query count
def get_global_query_count() -> int:
    supabase = get_supabase_client()
    response = supabase.table("global_counter").select("count").eq("id", 1).execute()
    
    if response.data and len(response.data) > 0:
        return response.data[0]["count"]
    return 0

# Increment the global query count safely
def increment_global_query_count() -> int:
    supabase = get_supabase_client()
    
    # Fetch current value
    response = supabase.table("global_counter").select("count").eq("id", 1).execute()
    
    if response.data and len(response.data) > 0:
        current = response.data[0]["count"]
        new_count = current + 1
        supabase.table("global_counter").update({"count": new_count}).eq("id", 1).execute()
    else:
        # Row doesn't exist yet, create it
        new_count = 1
        supabase.table("global_counter").insert({"id": 1, "count": new_count}).execute()
    
    return new_count
