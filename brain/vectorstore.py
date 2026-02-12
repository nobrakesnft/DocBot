"""
Vector Store
Simple vector store using numpy and local embeddings.
Works with Python 3.14+ (no ChromaDB dependency issues).
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
    """Simple vector store using local storage and API embeddings."""

    def __init__(self, persist_dir: str = None):
        self.persist_dir = persist_dir or config.CHROMA_PERSIST_DIR
        self.documents = []  # List of {"text": ..., "source": ..., "embedding": ...}
        self._load()

    def _get_embedding(self, text: str) -> List[float]:
        """Get embedding for text using Groq/OpenAI compatible API."""
        from litellm import embedding

        # Set API key
        os.environ["GROQ_API_KEY"] = config.GROQ_API_KEY

        try:
            # Use a small embedding model
            response = embedding(
                model="text-embedding-3-small",  # OpenAI embedding model
                input=[text]
            )
            return response.data[0]['embedding']
        except Exception as e:
            # Fallback: use simple hash-based pseudo-embedding
            # This is not ideal but works for testing
            return self._simple_embedding(text)

    def _simple_embedding(self, text: str) -> List[float]:
        """Simple fallback embedding using word hashing."""
        import hashlib

        # Create a simple 384-dim embedding from text
        words = text.lower().split()
        embedding = [0.0] * 384

        for i, word in enumerate(words):
            hash_val = int(hashlib.md5(word.encode()).hexdigest(), 16)
            for j in range(384):
                embedding[j] += ((hash_val >> (j % 32)) & 1) * 0.01

        # Normalize
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

    def add_documents(self, chunks: List[Dict]) -> int:
        """
        Add document chunks to the vector store.

        Args:
            chunks: List of dicts with 'text', 'source', 'chunk_index'

        Returns:
            Number of documents added
        """
        if not chunks:
            return 0

        print(f"Adding {len(chunks)} documents to vector store...")

        for i, chunk in enumerate(chunks):
            text = chunk["text"]

            # Get embedding
            embedding = self._simple_embedding(text)  # Use simple embedding for speed

            doc = {
                "text": text,
                "source": chunk.get("source", "unknown"),
                "chunk_index": chunk.get("chunk_index", i),
                "embedding": embedding
            }
            self.documents.append(doc)

            if (i + 1) % 10 == 0:
                print(f"  Processed {i + 1}/{len(chunks)} chunks...")

        # Save to disk
        self._save()

        print(f"Added {len(chunks)} documents. Total: {len(self.documents)}")
        return len(chunks)

    def search(self, query: str, top_k: int = None) -> List[Dict]:
        """
        Search for relevant documents.

        Args:
            query: The search query
            top_k: Number of results to return

        Returns:
            List of results with text, source, and similarity score
        """
        top_k = top_k or config.TOP_K_RESULTS

        if not self.documents:
            return []

        # Get query embedding
        query_embedding = self._simple_embedding(query)

        # Calculate similarities
        results = []
        for doc in self.documents:
            similarity = self._cosine_similarity(query_embedding, doc["embedding"])
            results.append({
                "text": doc["text"],
                "source": doc["source"],
                "similarity": similarity
            })

        # Sort by similarity (descending)
        results.sort(key=lambda x: x["similarity"], reverse=True)

        return results[:top_k]

    def get_context(self, query: str, top_k: int = None) -> str:
        """
        Get formatted context string for LLM.

        Args:
            query: The user's question
            top_k: Number of chunks to include

        Returns:
            Formatted context string
        """
        results = self.search(query, top_k)

        if not results:
            return "No relevant documentation found."

        context_parts = []
        for i, result in enumerate(results, 1):
            context_parts.append(
                f"[Source: {result['source']}]\n{result['text']}"
            )

        return "\n\n---\n\n".join(context_parts)

    def clear(self):
        """Delete all documents."""
        self.documents = []
        self._save()
        print("Cleared all documents.")

    def count(self) -> int:
        """Get the number of documents in the store."""
        return len(self.documents)

    def get_stats(self) -> Dict:
        """Get statistics about the vector store."""
        return {
            "collection_name": "docbot_docs",
            "document_count": self.count(),
            "persist_dir": self.persist_dir
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
                print(f"Loaded {len(self.documents)} documents from storage.")
            except Exception as e:
                print(f"Error loading documents: {e}")
                self.documents = []


# =============================================================================
# Quick Test
# =============================================================================

if __name__ == "__main__":
    from ingester import DocumentIngester

    # Initialize
    ingester = DocumentIngester()
    store = VectorStore()

    # Clear previous data
    store.clear()

    # Sample documents
    sample_text = """
    Welcome to CryptoProject!

    How to stake:
    1. Connect your wallet to app.cryptoproject.io
    2. Select the amount to stake
    3. Confirm the transaction
    4. Start earning 10% APY rewards!

    How to unstake:
    1. Go to the staking dashboard
    2. Click "Unstake"
    3. Wait for the 7-day unbonding period
    4. Claim your tokens

    Tokenomics:
    Total supply is 100 million tokens.
    Staking rewards come from protocol fees.
    """

    # Process and store
    print("Loading documents...")
    chunks = ingester.load_text(sample_text, source="sample_docs")
    print(f"Created {len(chunks)} chunks")

    print("\nAdding to vector store...")
    store.add_documents(chunks)
    print(f"Total documents: {store.count()}")

    # Test search
    print("\n--- Testing Search ---")
    test_queries = [
        "How do I stake my tokens?",
        "What is the APY?",
        "How long does unstaking take?"
    ]

    for query in test_queries:
        print(f"\nQuery: {query}")
        results = store.search(query, top_k=2)
        for r in results:
            print(f"  [{r['similarity']:.3f}] {r['text'][:60]}...")
