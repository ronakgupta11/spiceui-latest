import json
import os
from typing import Dict, Any, List
from langchain_huggingface import HuggingFaceEmbeddings
import sys
from pathlib import Path

# Add the parent directory to sys.path to import from app
sys.path.append(str(Path(__file__).parent.parent.parent))
from app.utils.chroma_vector_store import ComponentVectorStore

def ingest_icons():
    """Ingest icon documentation into vector store"""
    # Initialize vector store
    embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
    vector_store = ComponentVectorStore()

    # Load icon documentation
    script_dir = os.path.dirname(os.path.abspath(__file__))
    icon_docs_path = os.path.join(script_dir, "..", "..", "icon-docs", "icon-docs.json")
    
    with open(icon_docs_path, 'r') as f:
        icons = json.load(f)

    # Prepare and ingest each icon
    for icon in icons:

        
        
        # Add to vector store
        vector_store.add_icon(icon)

    print(f"Successfully ingested {len(icons)} icons into vector store")

if __name__ == "__main__":
    ingest_icons() 