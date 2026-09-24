import os

import requests
import streamlit as st


API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000/api")

st.set_page_config(page_title="P4 Production RAG", page_icon="📚", layout="wide")
st.title("P4 Production RAG")
st.caption("Local-first document Q&A with FastAPI, PostgreSQL/pgvector, Redis, and Ollama.")

if "messages" not in st.session_state:
    st.session_state.messages = []


def load_documents() -> list[dict]:
    try:
        response = requests.get(f"{API_BASE_URL}/documents", timeout=10)
        response.raise_for_status()
        return response.json()["documents"]
    except requests.RequestException:
        return []


with st.sidebar:
    st.header("Session")
    session_id = st.text_input("Session ID", value="demo-session")

    st.divider()
    st.header("Ingestion")
    files = st.file_uploader("Upload PDF files", type=["pdf"], accept_multiple_files=True)

    if st.button("Ingest PDFs", disabled=not files):
        with st.spinner("Uploading and indexing PDFs..."):
            response = requests.post(
                f"{API_BASE_URL}/ingest",
                files=[("files", (file.name, file.getvalue(), "application/pdf")) for file in files],
                timeout=300,
            )
        if response.ok:
            payload = response.json()
            st.success(f"Ingested {payload['total_documents']} document(s) and {payload['total_chunks']} chunks.")
        else:
            st.error(response.text)

    if st.button("Clear Session"):
        requests.delete(f"{API_BASE_URL}/sessions/{session_id}", timeout=10)
        st.session_state.messages = []
        st.rerun()

    st.divider()
    st.header("Uploaded Documents")
    documents = load_documents()
    if documents:
        for item in documents:
            st.write(f"- {item['filename']} ({item['chunk_count']} chunks)")
    else:
        st.caption("No documents ingested yet.")

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        display_text = message.get("content") or message.get("answer") or ""
        st.write(display_text)
        if message["role"] == "assistant":
            st.caption(
                f"Latency: {message['latency_ms']:.2f} ms | "
                f"Retrieved chunks: {message['retrieved_chunks_count']}"
            )
            with st.expander("Sources"):
                for source in message["sources"]:
                    st.markdown(
                        f"**{source['filename']}** | page {source['page_number']} | chunk {source['chunk_index']}"
                    )
                    st.write(source["preview"])

question = st.chat_input("Ask a question about your uploaded documents")

if question:
    st.session_state.messages.append({"role": "user", "content": question})

    with st.chat_message("user"):
        st.write(question)

    with st.chat_message("assistant"):
        with st.spinner("Retrieving answer..."):
            response = requests.post(
                f"{API_BASE_URL}/query",
                json={"question": question, "session_id": session_id},
                timeout=180,
            )

        if response.ok:
            payload = response.json()
            st.write(payload["answer"])
            st.caption(
                f"Latency: {payload['latency_ms']:.2f} ms | "
                f"Retrieved chunks: {payload['retrieved_chunks_count']}"
            )
            with st.expander("Sources"):
                for source in payload["sources"]:
                    st.markdown(
                        f"**{source['filename']}** | page {source['page_number']} | chunk {source['chunk_index']}"
                    )
                    st.write(source["preview"])
            st.session_state.messages.append(
                {"role": "assistant", "content": payload["answer"], **payload}
            )
        else:
            st.error(response.text)
