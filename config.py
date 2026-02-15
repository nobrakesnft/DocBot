"""
DocBot Configuration
Loads environment variables and sets up configuration.
"""

import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# =============================================================================
# LLM Configuration
# =============================================================================

# Switch between providers by changing this line:
# - "groq/llama-3.3-70b-versatile"  (Free, fast)
# - "groq/mixtral-8x7b-32768"       (Free, fast)
# - "gpt-4o-mini"                    (Cheap, good)
# - "gpt-4o"                         (Best quality)

LLM_MODEL = "groq/llama-3.3-70b-versatile"

# API Keys
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# =============================================================================
# Bot Tokens
# =============================================================================

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
DISCORD_BOT_TOKEN = os.getenv("DISCORD_BOT_TOKEN")

# =============================================================================
# Vector Database Configuration
# =============================================================================

# Where to store the ChromaDB database
CHROMA_PERSIST_DIR = os.path.join(os.path.dirname(__file__), "data", "chroma_db")

# Collection name for storing document embeddings
CHROMA_COLLECTION_NAME = "docbot_docs"

# =============================================================================
# Document Processing Configuration
# =============================================================================

# How many characters per chunk (smaller = more precise, larger = more context)
CHUNK_SIZE = 500

# Overlap between chunks (helps maintain context)
CHUNK_OVERLAP = 50

# How many relevant chunks to retrieve for each question
# Higher = more context but slightly more tokens
TOP_K_RESULTS = 5

# =============================================================================
# Bot Behavior Configuration
# =============================================================================

# System prompt for the AI - production-ready for Web3 communities
SYSTEM_PROMPT = """You answer questions about the project using ONLY the context provided below.

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

TONE:
- Casual, friendly, short (1-3 sentences)
- 1 emoji max
- No corporate speak

ONLY SAY "not in the docs" WHEN:
- You searched the context AND found nothing relevant
- There's truly no date/fact/info provided

Context from docs:
{context}
"""

# LLM temperature - lower = more consistent, higher = more varied
# Using 0.5 for balance between consistency and natural tone
LLM_TEMPERATURE = 0.5

# =============================================================================
# Tone Mode Configuration
# =============================================================================

# Tone instructions injected into system prompt based on project setting
TONE_INSTRUCTIONS = {
    "casual": """TONE:
- Casual, friendly, web3-native
- Light slang allowed (ser, fam, ngl, etc.)
- 1 emoji max
- No corporate speak
- Example: "No exact date yet, snapshot is planned for Q2 2026." """,

    "neutral": """TONE:
- Friendly but clean
- No slang or web3 lingo
- No emojis
- Approachable but clear
- Example: "Snapshot is planned for Q2 2026, but no exact date has been announced yet." """,

    "professional": """TONE:
- Formal support tone
- No emojis, no slang
- Clear and precise language
- Example: "The snapshot is scheduled for Q2 2026. An exact date has not yet been announced." """,
}

# Default tone for new projects
DEFAULT_TONE = "casual"

# =============================================================================
# Multi-Topic Formatting
# =============================================================================

# Instruction added when multiple topics detected in a question
MULTI_TOPIC_INSTRUCTION = """
FORMATTING (Multiple topics detected):
- Break your answer into short labeled sections
- Each section: 1-2 sentences max
- Use this format:
  **Topic:**
  Short answer here.

- Keep total response to 4-6 lines
- No long paragraphs
"""

# Confidence threshold - if similarity is below this, don't guess
# 0.30 = stricter, less likely to give wrong answers
CONFIDENCE_THRESHOLD = 0.30

# =============================================================================
# Validation
# =============================================================================

def validate_config():
    """Check that required config values are set."""
    errors = []

    if not GROQ_API_KEY or GROQ_API_KEY == "your_groq_api_key_here":
        errors.append("GROQ_API_KEY not set in .env file")

    return errors

if __name__ == "__main__":
    # Quick test
    errors = validate_config()
    if errors:
        print("Configuration errors:")
        for e in errors:
            print(f"  - {e}")
    else:
        print("Configuration OK!")
        print(f"Using model: {LLM_MODEL}")
