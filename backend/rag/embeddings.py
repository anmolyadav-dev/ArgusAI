"""
RAG Embeddings — Build and manage the local vector store.

Uses ChromaDB for local vector storage and sentence-transformers
for generating embeddings. No external APIs needed.
"""

import json
from pathlib import Path
import chromadb
from chromadb.config import Settings as ChromaSettings

from backend.config import settings


def build_knowledge_base():
    """
    Load CVE, CWE, and OWASP data and store as embeddings in ChromaDB.
    
    This should be run once on first startup or when knowledge is updated.
    Each document becomes a vector that can be searched by similarity.
    """
    knowledge_dir = Path(settings.knowledge_dir)

    # Initialize ChromaDB with local persistence
    client = chromadb.PersistentClient(
        path=settings.chroma_persist_dir,
        settings=chromadb.config.Settings(anonymized_telemetry=False)
    )

    # Create or get the collection
    # ChromaDB handles embedding via its default embedding function
    # We'll use the default all-MiniLM-L6-v2 model
    collection = client.get_or_create_collection(
        name="security_knowledge",
        metadata={"description": "CVE, CWE, and OWASP knowledge base"},
    )

    # Check if already populated
    if collection.count() > 0:
        print(f"Knowledge base already has {collection.count()} documents. Skipping.")
        return collection

    documents = []
    metadatas = []
    ids = []



    # --- Load CWE data ---
    cwe_path = knowledge_dir / "cwe_data.json"
    if cwe_path.exists():
        with open(cwe_path) as f:
            cwes = json.load(f)
        for cwe in cwes:
            doc = (
                f"{cwe['id']} - {cwe['name']}: {cwe['description']} "
                f"Impact: {cwe['impact']} "
                f"Mitigation: {cwe['mitigation']}"
            )
            documents.append(doc)
            metadatas.append({
                "type": "cwe",
                "id": cwe["id"],
                "name": cwe["name"],
            })
            ids.append(cwe["id"])

    # --- Load OWASP data ---
    owasp_path = knowledge_dir / "owasp_top10.json"
    if owasp_path.exists():
        with open(owasp_path) as f:
            owasp = json.load(f)
        for item in owasp:
            vulns = ", ".join(item.get("common_vulnerabilities", []))
            prevention = ", ".join(item.get("prevention", []))
            doc = (
                f"{item['id']} - {item['name']}: {item['description']} "
                f"Common vulnerabilities: {vulns}. "
                f"Prevention: {prevention}."
            )
            documents.append(doc)
            metadatas.append({
                "type": "owasp",
                "id": item["id"],
                "name": item["name"],
            })
            ids.append(item["id"])

    # Add all documents to ChromaDB
    if documents:
        collection.add(
            documents=documents,
            metadatas=metadatas,
            ids=ids,
        )
        print(f"Added {len(documents)} documents to knowledge base.")

    return collection


def get_collection():
    """
    Get the existing collection.
    """
    client = chromadb.PersistentClient(
        path=settings.chroma_persist_dir,
        settings=chromadb.config.Settings(anonymized_telemetry=False)
    )
    return client.get_collection(name="security_knowledge")
