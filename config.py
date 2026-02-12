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
TOP_K_RESULTS = 3

# =============================================================================
# Bot Behavior Configuration
# =============================================================================

# System prompt for the AI
SYSTEM_PROMPT = """You are DocBot, a helpful AI assistant for a crypto/web3 project.
You answer questions based ONLY on the documentation provided to you.

Rules:
1. Only answer based on the provided context
2. If you don't know the answer, say "I'm not sure about that. Please ask a team member."
3. Be concise and helpful
4. Use a friendly, professional tone
5. If asked about prices, dates, or specifics not in the docs, say you don't have that information

Context from documentation:
{context}
"""

# Confidence threshold - if similarity is below this, say "I don't know"
CONFIDENCE_THRESHOLD = 0.3

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
