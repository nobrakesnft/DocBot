"""
Answerer
Generates answers using LLM based on retrieved context.
"""

import os
from typing import Optional

# Add parent directory to path for imports
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import config
from brain.vectorstore import VectorStore


class Answerer:
    """Generates answers using LLM and vector search."""

    def __init__(self, vector_store: VectorStore = None):
        self.vector_store = vector_store or VectorStore()
        self._validate_api_key()

    def _validate_api_key(self):
        """Ensure API key is configured."""
        if not config.GROQ_API_KEY or config.GROQ_API_KEY == "your_groq_api_key_here":
            raise ValueError(
                "GROQ_API_KEY not configured. Please add it to your .env file."
            )

    def answer(self, question: str, top_k: int = None) -> dict:
        """
        Answer a question using RAG (Retrieval Augmented Generation).

        Args:
            question: The user's question
            top_k: Number of context chunks to use

        Returns:
            Dict with 'answer', 'sources', and 'confidence'
        """
        # Get relevant context
        results = self.vector_store.search(question, top_k)

        if not results:
            return {
                "answer": "I don't have any documentation loaded yet. Please ask an admin to add some docs!",
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
        context = self.vector_store.get_context(question, top_k)

        # Generate answer
        answer_text = self._generate_answer(question, context)

        return {
            "answer": answer_text,
            "sources": list(set(r["source"] for r in results)),
            "confidence": avg_similarity
        }

    def _generate_answer(self, question: str, context: str) -> str:
        """
        Generate an answer using the LLM.

        Args:
            question: The user's question
            context: Retrieved document context

        Returns:
            The generated answer
        """
        from litellm import completion

        # Set API key for Groq
        os.environ["GROQ_API_KEY"] = config.GROQ_API_KEY

        # Build the prompt
        system_prompt = config.SYSTEM_PROMPT.format(context=context)

        try:
            response = completion(
                model=config.LLM_MODEL,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": question}
                ],
                max_tokens=500,
                temperature=0.3  # Lower = more focused answers
            )

            return response.choices[0].message.content.strip()

        except Exception as e:
            print(f"LLM Error: {e}")
            return "Sorry, I encountered an error generating a response. Please try again."

    def simple_answer(self, question: str) -> str:
        """
        Simple interface - just returns the answer text.

        Args:
            question: The user's question

        Returns:
            The answer string
        """
        result = self.answer(question)
        return result["answer"]


# =============================================================================
# Quick Test
# =============================================================================

if __name__ == "__main__":
    from ingester import DocumentIngester
    from vectorstore import VectorStore

    print("Testing Answerer...")
    print("=" * 50)

    # Initialize components
    ingester = DocumentIngester()
    store = VectorStore()

    # Add sample docs
    sample_text = """
    Welcome to CryptoProject!

    How to stake:
    1. Connect your wallet to app.cryptoproject.io
    2. Click on the "Stake" tab
    3. Enter the amount you want to stake
    4. Confirm the transaction in your wallet
    5. Start earning 10% APY rewards!

    How to unstake:
    1. Go to the staking dashboard
    2. Click "Unstake"
    3. Wait for the 7-day unbonding period
    4. Claim your tokens

    Supported wallets:
    - MetaMask
    - WalletConnect
    - Coinbase Wallet

    Minimum stake: 100 tokens
    Maximum stake: No limit
    """

    print("Loading sample documentation...")
    chunks = ingester.load_text(sample_text, source="staking_guide")
    store.add_documents(chunks)
    print(f"Loaded {store.count()} chunks\n")

    # Test the answerer
    answerer = Answerer(store)

    test_questions = [
        "How do I stake my tokens?",
        "What wallets are supported?",
        "What is the minimum stake amount?",
        "How long does unstaking take?"
    ]

    for q in test_questions:
        print(f"Q: {q}")
        result = answerer.answer(q)
        print(f"A: {result['answer']}")
        print(f"   Confidence: {result['confidence']:.2f}")
        print(f"   Sources: {result['sources']}")
        print()
