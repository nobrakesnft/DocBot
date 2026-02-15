"""
Answerer (Multi-Tenant)
Generates answers using LLM based on project-specific context.
Production-ready with token logging and consistent responses.
"""

import os
import random
import time
from typing import Optional, Dict

# Add parent directory to path for imports
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import config
from brain.vectorstore import VectorStore


# Token usage tracking per project
_token_usage: Dict[str, Dict] = {}


def get_token_usage(project_id: str = None) -> Dict:
    """Get token usage stats for a project or all projects."""
    if project_id:
        return _token_usage.get(project_id, {"input": 0, "output": 0, "requests": 0})
    return _token_usage


def log_token_usage(project_id: str, input_tokens: int, output_tokens: int):
    """Log token usage for a project."""
    if project_id not in _token_usage:
        _token_usage[project_id] = {"input": 0, "output": 0, "requests": 0}

    _token_usage[project_id]["input"] += input_tokens
    _token_usage[project_id]["output"] += output_tokens
    _token_usage[project_id]["requests"] += 1


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

    NO_DOCS_RESPONSES = [
        "no docs loaded yet - an admin needs to add some first",
        "docs haven't been set up yet - ping an admin to load them",
    ]

    def _generate_unknown_response(self, question: str, project_id: str = "default") -> str:
        """
        Generate a smart, contextual response when docs don't have the answer.
        Uses LLM for natural response but keeps it short.
        """
        from litellm import completion
        from connectors.bot_utils import extract_topic

        os.environ["GROQ_API_KEY"] = config.GROQ_API_KEY

        topic = extract_topic(question)

        prompt = f"""The user asked about "{topic}" but this info isn't in the project docs.

Generate a SHORT (1 sentence max) casual response that:
- Says you don't have that info
- Suggests checking official announcements
- Sounds like a helpful community member, not a bot
- No corporate speak, no "I apologize"

Examples of good responses:
- "hmm {topic} isn't in what i've got, maybe check announcements"
- "don't have anything on {topic} rn - team announcements would have it"
- "not seeing {topic} in the docs, keep an eye on official channels"

Respond with ONLY the message, nothing else."""

        try:
            response = completion(
                model=config.LLM_MODEL,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=40,  # Very short
                temperature=0.7  # Slightly varied
            )

            # Log tokens
            usage = response.usage
            if usage:
                log_token_usage(project_id,
                    getattr(usage, 'prompt_tokens', 0),
                    getattr(usage, 'completion_tokens', 0))

            return response.choices[0].message.content.strip().strip('"')

        except Exception as e:
            print(f"Unknown response LLM error: {e}")
            return f"hmm {topic} isn't in the docs - check announcements for updates"

    def _build_system_prompt(self, context: str, tone_mode: str = "casual", multi_topic: bool = False) -> str:
        """
        Build dynamic system prompt based on tone and multi-topic detection.

        PATCH 1: Adds multi-topic formatting instruction
        PATCH 2: Injects tone-specific instructions
        """
        # Base prompt without the TONE section
        base_prompt = """You answer questions about the project using ONLY the context provided below.

CRITICAL RULES - READ CAREFULLY:
1. If the context contains ANY specific date, timeframe, number, or fact - you MUST include it
2. "Q2 2026" is a fact - ALWAYS mention it, don't say "no date yet"
3. "2-4 weeks" is a fact - ALWAYS mention it
4. Scan the ENTIRE context for relevant facts before answering
5. If context says "planned for Q2" - say "planned for Q2", not "no exact date"

WRONG vs RIGHT:
- WRONG: "no exact date confirmed yet" (when context says Q2 2026)
- RIGHT: "Q2 2026 is planned, no exact day announced yet"
- WRONG: "check announcements" (when context has the answer)
- RIGHT: Include the actual fact from context

ONLY SAY "not in the docs" WHEN:
- You searched the context AND found nothing relevant
- There's truly no date/fact/info provided
"""

        # Add tone instruction (PATCH 2)
        tone_instruction = config.TONE_INSTRUCTIONS.get(tone_mode, config.TONE_INSTRUCTIONS["casual"])

        # Add multi-topic instruction if needed (PATCH 1)
        multi_topic_instruction = ""
        if multi_topic:
            multi_topic_instruction = config.MULTI_TOPIC_INSTRUCTION

        # Build final prompt
        system_prompt = f"""{base_prompt}
{tone_instruction}
{multi_topic_instruction}
Context from docs:
{context}
"""
        return system_prompt

    def answer(self, question: str, project_id: str = "default", top_k: int = None) -> dict:
        """
        Answer a question using RAG for a specific project.

        Args:
            question: The user's question
            project_id: Which project's docs to search
            top_k: Number of context chunks to use

        Returns:
            Dict with 'answer', 'sources', 'confidence', and 'intent'
        """
        # Extract intent for tracking
        from connectors.bot_utils import extract_intent, is_multi_topic, get_project_tone
        intent = extract_intent(question)

        # PATCH 1 & 2: Get tone and check for multi-topic
        tone_mode = get_project_tone(project_id)
        multi_topic = is_multi_topic(question)

        # Get relevant context for this project
        results = self.vector_store.search(question, project_id=project_id, top_k=top_k)

        if not results:
            return {
                "answer": random.choice(self.NO_DOCS_RESPONSES),
                "sources": [],
                "confidence": 0,
                "intent": intent
            }

        # Check confidence - if too low, don't guess
        avg_similarity = sum(r["similarity"] for r in results) / len(results)
        max_similarity = max(r["similarity"] for r in results)

        if max_similarity < config.CONFIDENCE_THRESHOLD:
            # Generate smart contextual "I don't know" response
            unknown_response = self._generate_unknown_response(question, project_id)
            return {
                "answer": unknown_response,
                "sources": [r["source"] for r in results],
                "confidence": avg_similarity,
                "intent": intent
            }

        # Build context from relevant docs
        context = self.vector_store.get_context(question, project_id=project_id, top_k=top_k)

        # Generate answer with token tracking
        # PATCH 1 & 2: Pass tone_mode and multi_topic
        answer_text, tokens = self._generate_answer(
            question, context, project_id,
            tone_mode=tone_mode, multi_topic=multi_topic
        )

        # Add subtle closing (20% chance, keeps it natural)
        if random.random() < 0.2:
            closings = [" 👍", " hope that helps"]
            closing = random.choice(closings)
            if not answer_text.rstrip().endswith(('!', '?', '👍', '.', 'helps')):
                answer_text = answer_text.rstrip() + closing

        return {
            "answer": answer_text,
            "sources": list(set(r["source"] for r in results)),
            "confidence": avg_similarity,
            "intent": intent
        }

    def _generate_answer(
        self, question: str, context: str, project_id: str = "default",
        tone_mode: str = "casual", multi_topic: bool = False
    ) -> tuple[str, dict]:
        """
        Generate an answer using the LLM.

        Args:
            question: The user's question
            context: Retrieved context from docs
            project_id: Project identifier
            tone_mode: One of 'casual', 'neutral', 'professional'
            multi_topic: Whether multiple topics detected

        Returns:
            (answer_text, token_info)
        """
        from litellm import completion

        os.environ["GROQ_API_KEY"] = config.GROQ_API_KEY

        # PATCH 1 & 2: Build dynamic system prompt
        system_prompt = self._build_system_prompt(context, tone_mode, multi_topic)

        # Lower temperature for more consistent answers
        temperature = getattr(config, 'LLM_TEMPERATURE', 0.5)

        try:
            response = completion(
                model=config.LLM_MODEL,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": question}
                ],
                max_tokens=150,  # Enforce short responses (1-3 sentences)
                temperature=temperature
            )

            # Log token usage
            usage = response.usage
            if usage:
                input_tokens = getattr(usage, 'prompt_tokens', 0)
                output_tokens = getattr(usage, 'completion_tokens', 0)
                log_token_usage(project_id, input_tokens, output_tokens)
                tokens = {"input": input_tokens, "output": output_tokens}
            else:
                tokens = {"input": 0, "output": 0}

            return response.choices[0].message.content.strip(), tokens

        except Exception as e:
            print(f"LLM Error: {e}")
            error_responses = [
                "something went wrong, try again?",
                "hit an error - mind asking again?",
            ]
            return random.choice(error_responses), {"input": 0, "output": 0}

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
