"""
Answerer (Multi-Tenant)
Generates answers using LLM based on project-specific context.
"""

import os
from typing import Optional

# Add parent directory to path for imports
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import config
from brain.vectorstore import VectorStore


class Answerer:
    """Generates answers using LLM and project-specific vector search."""

    def __init__(self, vector_store: VectorStore = None):
        self.vector_store = vector_store or VectorStore()
        self._validate_api_key()

    def _validate_api_key(self):
        """Ensure API key is configured."""
        if not config.GROQ_API_KEY or config.GROQ_API_KEY == "your_groq_api_key_here":
            raise ValueError(
                "GROQ_API_KEY not configured. Please add it to your .env file."
            )

    def answer(self, question: str, project_id: str = "default", top_k: int = None) -> dict:
        """
        Answer a question using RAG for a specific project.

        Args:
            question: The user's question
            project_id: Which project's docs to search
            top_k: Number of context chunks to use

        Returns:
            Dict with 'answer', 'sources', and 'confidence'
        """
        # Get relevant context for this project
        results = self.vector_store.search(question, project_id=project_id, top_k=top_k)

        if not results:
            return {
                "answer": "I don't have any documentation loaded for this server yet. Please ask an admin to add docs!",
                "sources": [],
                "confidence": 0
            }

        # Check confidence
        avg_similarity = sum(r["similarity"] for r in results) / len(results)

        if avg_similarity < config.CONFIDENCE_THRESHOLD:
            return {
                "answer": "I'm not sure about that based on the documentation I have. Please ask a team member for help!",
                "sources": [r["source"] for r in results],
                "confidence": avg_similarity
            }

        # Build context
        context = self.vector_store.get_context(question, project_id=project_id, top_k=top_k)

        # Generate answer
        answer_text = self._generate_answer(question, context)

        return {
            "answer": answer_text,
            "sources": list(set(r["source"] for r in results)),
            "confidence": avg_similarity
        }

    def _generate_answer(self, question: str, context: str) -> str:
        """Generate an answer using the LLM."""
        from litellm import completion

        os.environ["GROQ_API_KEY"] = config.GROQ_API_KEY

        system_prompt = config.SYSTEM_PROMPT.format(context=context)

        try:
            response = completion(
                model=config.LLM_MODEL,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": question}
                ],
                max_tokens=500,
                temperature=0.3
            )

            return response.choices[0].message.content.strip()

        except Exception as e:
            print(f"LLM Error: {e}")
            return "Sorry, I encountered an error generating a response. Please try again."

    def simple_answer(self, question: str, project_id: str = "default") -> str:
        """Simple interface - just returns the answer text."""
        result = self.answer(question, project_id=project_id)
        return result["answer"]


# =============================================================================
# Quick Test
# =============================================================================

if __name__ == "__main__":
    from ingester import DocumentIngester
    from vectorstore import VectorStore

    print("Testing Multi-Tenant Answerer...")
    print("=" * 50)

    ingester = DocumentIngester()
    store = VectorStore()

    # Clear and add test docs
    store.clear()

    # Project A docs
    chunks_a = ingester.load_text("""
    Welcome to ProjectA!
    We offer 10% APY staking on Ethereum.
    Supported wallets: MetaMask, WalletConnect.
    Minimum stake: 100 tokens.
    """, source="projecta_docs")
    store.add_documents(chunks_a, project_id="server_a")

    # Project B docs
    chunks_b = ingester.load_text("""
    Welcome to ProjectB!
    We offer 20% APY staking on Solana.
    Supported wallets: Phantom, Solflare.
    Minimum stake: 50 tokens.
    """, source="projectb_docs")
    store.add_documents(chunks_b, project_id="server_b")

    # Test answerer
    answerer = Answerer(store)

    print("\n--- Question: 'What is the APY?' ---")

    print("\nAsking Server A:")
    result = answerer.answer("What is the APY?", project_id="server_a")
    print(f"  Answer: {result['answer']}")

    print("\nAsking Server B:")
    result = answerer.answer("What is the APY?", project_id="server_b")
    print(f"  Answer: {result['answer']}")
