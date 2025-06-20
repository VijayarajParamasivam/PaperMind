import os
from pypdf import PdfReader

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

def create_vector_database(texts, chroma_client, collection_name="pdf_collection"):
    try:
        chroma_client.delete_collection(name=collection_name)
    except Exception:
        pass
    collection = chroma_client.create_collection(name=collection_name)
    ids = [f"id{i+1}" for i in range(len(texts))]
    collection.add(documents=texts, ids=ids)
    return collection

def delete_temp_files(file_path):
    if os.path.exists(file_path):
        os.remove(file_path)