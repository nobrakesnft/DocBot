"""
Vector Store (Multi-Tenant)
Supports multiple projects with isolated document stores.
Each project (server/group) has its own documents.
"""

import os
import json
import pickle
from typing import List, Dict, Optional

# Add parent directory to path for imports
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import config


class VectorStore:
    """Multi-tenant vector store - each project has isolated docs."""

    def __init__(self, persist_dir: str = None):
        self.persist_dir = persist_dir or config.CHROMA_PERSIST_DIR
        self.documents = []  # List of {"text": ..., "source": ..., "project_id": ..., "embedding": ...}
        self._load()

    def _simple_embedding(self, text: str) -> List[float]:
        """Simple embedding using word hashing."""
        import hashlib

        words = text.lower().split()
        embedding = [0.0] * 384

        for i, word in enumerate(words):
            hash_val = int(hashlib.md5(word.encode()).hexdigest(), 16)
            for j in range(384):
                embedding[j] += ((hash_val >> (j % 32)) & 1) * 0.01

        magnitude = sum(x*x for x in embedding) ** 0.5
        if magnitude > 0:
            embedding = [x / magnitude for x in embedding]

        return embedding

    def _cosine_similarity(self, a: List[float], b: List[float]) -> float:
        """Calculate cosine similarity between two vectors."""
        dot_product = sum(x * y for x, y in zip(a, b))
        magnitude_a = sum(x * x for x in a) ** 0.5
        magnitude_b = sum(x * x for x in b) ** 0.5

        if magnitude_a == 0 or magnitude_b == 0:
            return 0.0

        return dot_product / (magnitude_a * magnitude_b)

    def add_documents(self, chunks: List[Dict], project_id: str = "default") -> int:
        """
        Add document chunks for a specific project.

        Args:
            chunks: List of dicts with 'text', 'source'
            project_id: Unique identifier for the project (server_id, group_id, etc.)

        Returns:
            Number of documents added
        """
        if not chunks:
            return 0

        print(f"Adding {len(chunks)} documents for project: {project_id}")

        for i, chunk in enumerate(chunks):
            text = chunk["text"]
            embedding = self._simple_embedding(text)

            doc = {
                "text": text,
                "source": chunk.get("source", "unknown"),
                "chunk_index": chunk.get("chunk_index", i),
                "project_id": project_id,  # Multi-tenant key
                "embedding": embedding
            }
            self.documents.append(doc)

        self._save()
        print(f"Added {len(chunks)} documents. Total: {len(self.documents)}")
        return len(chunks)

    def search(self, query: str, project_id: str = "default", top_k: int = None) -> List[Dict]:
        """
        Search for relevant documents within a specific project.

        Args:
            query: The search query
            project_id: Only search this project's documents
            top_k: Number of results to return

        Returns:
            List of results with text, source, and similarity score
        """
        top_k = top_k or config.TOP_K_RESULTS

        # Filter documents by project_id
        project_docs = [d for d in self.documents if d.get("project_id") == project_id]

        if not project_docs:
            return []

        query_embedding = self._simple_embedding(query)

        results = []
        for doc in project_docs:
            similarity = self._cosine_similarity(query_embedding, doc["embedding"])
            results.append({
                "text": doc["text"],
                "source": doc["source"],
                "similarity": similarity
            })

        results.sort(key=lambda x: x["similarity"], reverse=True)
        return results[:top_k]

    def get_context(self, query: str, project_id: str = "default", top_k: int = None) -> str:
        """Get formatted context string for LLM."""
        results = self.search(query, project_id, top_k)

        if not results:
            return "No relevant documentation found for this project."

        context_parts = []
        for result in results:
            context_parts.append(f"[Source: {result['source']}]\n{result['text']}")

        return "\n\n---\n\n".join(context_parts)

    def clear_project(self, project_id: str):
        """Delete all documents for a specific project."""
        before_count = len(self.documents)
        self.documents = [d for d in self.documents if d.get("project_id") != project_id]
        after_count = len(self.documents)
        self._save()
        removed = before_count - after_count
        print(f"Cleared {removed} documents for project: {project_id}")
        return removed

    def clear(self):
        """Delete ALL documents (all projects)."""
        self.documents = []
        self._save()
        print("Cleared all documents.")

    def count(self, project_id: str = None) -> int:
        """Get document count (optionally filtered by project)."""
        if project_id:
            return len([d for d in self.documents if d.get("project_id") == project_id])
        return len(self.documents)

    def list_projects(self) -> List[Dict]:
        """List all projects and their document counts."""
        projects = {}
        for doc in self.documents:
            pid = doc.get("project_id", "default")
            if pid not in projects:
                projects[pid] = {"project_id": pid, "doc_count": 0, "sources": set()}
            projects[pid]["doc_count"] += 1
            projects[pid]["sources"].add(doc.get("source", "unknown"))

        # Convert sets to lists for JSON serialization
        result = []
        for pid, data in projects.items():
            result.append({
                "project_id": pid,
                "doc_count": data["doc_count"],
                "sources": list(data["sources"])
            })

        return result

    def get_stats(self, project_id: str = None) -> Dict:
        """Get statistics about the vector store."""
        if project_id:
            return {
                "project_id": project_id,
                "document_count": self.count(project_id),
                "total_documents": self.count()
            }
        return {
            "total_documents": self.count(),
            "projects": self.list_projects()
        }

    def _save(self):
        """Save documents to disk."""
        os.makedirs(self.persist_dir, exist_ok=True)
        filepath = os.path.join(self.persist_dir, "documents.pkl")
        with open(filepath, "wb") as f:
            pickle.dump(self.documents, f)

    def _load(self):
        """Load documents from disk."""
        filepath = os.path.join(self.persist_dir, "documents.pkl")
        if os.path.exists(filepath):
            try:
                with open(filepath, "rb") as f:
                    self.documents = pickle.load(f)

                # Migration: add project_id to old documents if missing
                for doc in self.documents:
                    if "project_id" not in doc:
                        doc["project_id"] = "default"

                print(f"Loaded {len(self.documents)} documents from storage.")
            except Exception as e:
                print(f"Error loading documents: {e}")
                self.documents = []


# =============================================================================
# Quick Test
# =============================================================================

if __name__ == "__main__":
    store = VectorStore()

    # Test multi-tenant
    print("\n=== Testing Multi-Tenant Vector Store ===\n")

    # Clear all
    store.clear()

    # Add docs for Project A
    store.add_documents([
        {"text": "Project A stakes at 10% APY on Ethereum.", "source": "project_a.md"},
        {"text": "Project A uses MetaMask wallet.", "source": "project_a.md"},
    ], project_id="project_a")

    # Add docs for Project B
    store.add_documents([
        {"text": "Project B stakes at 15% APY on Solana.", "source": "project_b.md"},
        {"text": "Project B uses Phantom wallet.", "source": "project_b.md"},
    ], project_id="project_b")

    # Test search isolation
    print("\n--- Search 'APY' in Project A ---")
    results = store.search("What is the APY?", project_id="project_a")
    for r in results:
        print(f"  [{r['similarity']:.3f}] {r['text']}")

    print("\n--- Search 'APY' in Project B ---")
    results = store.search("What is the APY?", project_id="project_b")
    for r in results:
        print(f"  [{r['similarity']:.3f}] {r['text']}")

    print("\n--- List Projects ---")
    for p in store.list_projects():
        print(f"  {p['project_id']}: {p['doc_count']} docs from {p['sources']}")
