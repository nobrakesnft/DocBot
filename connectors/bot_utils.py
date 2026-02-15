"""
Shared Bot Utilities
Common logic for Discord and Telegram bots to ensure consistent, human-like behavior.
"""

import time
import random
import asyncio
import json
import os
from typing import Dict, Optional, List

# =============================================================================
# CONFIGURATION
# =============================================================================

# Cooldown between questions per user (seconds)
USER_COOLDOWN = 15

# Typing delay range (seconds) - makes bot feel human
TYPING_DELAY_MIN = 0.8
TYPING_DELAY_MAX = 2.5

# =============================================================================
# PATTERNS
# =============================================================================

# Messages to ignore completely (greetings, reactions, etc.)
IGNORE_PATTERNS = [
    # Greetings
    'gm', 'gn', 'GM', 'GN', 'good morning', 'good night',
    # Web3 vibes
    'wagmi', 'ngmi', 'lfg', 'LFG', 'WAGMI',
    # Reactions
    'lol', 'lmao', 'haha', 'hahaha', 'kek', 'lmfao',
    'nice', 'cool', 'wow', 'dope', 'based', 'sick',
    # Gratitude (already helped)
    'thanks', 'thank you', 'thx', 'ty', 'tysm', 'appreciated',
    # Acknowledgments
    'ok', 'okay', 'k', 'kk', 'got it', 'understood', 'makes sense',
    'yep', 'yup', 'yeah', 'yes', 'no', 'nope', 'nah',
    # Emojis only
    '👍', '🙏', '❤️', '🔥', '💯', '😂', '🚀',
]

# Signals that indicate a question
QUESTION_SIGNALS = [
    '?',  # Direct question mark
    'how do', 'how can', 'how to', 'how does', 'how is',
    'what is', 'what are', 'what does', "what's", 'whats',
    'where do', 'where can', 'where is', "where's",
    'when do', 'when can', 'when is', 'when does',
    'why do', 'why does', 'why is', "why's",
    'can i', 'can you', 'could i', 'could you',
    'do i', 'do you', 'does it', 'does the',
    'is it', 'is there', 'is the', 'are there', 'are the',
    'should i', 'would it', 'will it', 'will the',
    'tell me', 'explain', 'help me', 'need help',
    'anyone know', 'does anyone', 'has anyone',
    # Crypto slang
    'wen ', 'wen?',  # "wen airdrop", "wen?"
]

# =============================================================================
# RATE LIMITING
# =============================================================================

# Track last question time per user
_user_cooldowns: Dict[str, float] = {}


# =============================================================================
# QUESTION CACHE (Duplicate Detection)
# =============================================================================

# Cache structure: project_id -> list of {question, answer, message_ref, timestamp, user_id, intent}
_question_cache: Dict[str, list] = {}

# Track repeat counts: cache_key (channel:topic) -> count
_repeat_counts: Dict[str, int] = {}

# Track repeat timestamps for auto-reset
_repeat_timestamps: Dict[str, float] = {}

# Reset repeat count after this many seconds
REPEAT_RESET_WINDOW = 600  # 10 minutes

# How long to keep cached answers (seconds)
CACHE_EXPIRY = 3600  # 1 hour

# Duplicate suppression window (seconds) - same intent in same channel
DUPLICATE_WINDOW = 600  # 10 minutes

# How many recent Q&As to keep per project
CACHE_SIZE = 50

# Similarity threshold for considering questions as duplicates (0-1)
SIMILARITY_THRESHOLD = 0.80

# =============================================================================
# INTENT EXTRACTION
# =============================================================================

# Common intents to normalize questions
INTENT_KEYWORDS = {
    'airdrop': ['airdrop', 'drop', 'free tokens', 'claim'],
    'snapshot': ['snapshot', 'snap'],
    'tge': ['tge', 'token generation', 'token launch'],
    'listing': ['listing', 'listed', 'exchange', 'cex', 'dex'],
    'staking': ['stake', 'staking', 'apy', 'yield'],
    'tokenomics': ['tokenomics', 'supply', 'allocation', 'vesting'],
    'roadmap': ['roadmap', 'timeline', 'when', 'wen', 'date'],
    'wallet': ['wallet', 'connect', 'metamask', 'phantom'],
    'price': ['price', 'cost', 'how much'],
    'eligibility': ['eligible', 'eligibility', 'qualify', 'criteria'],
}

# =============================================================================
# PROJECT SETTINGS (Tone Mode per Project)
# =============================================================================

# In-memory storage for project settings
_project_settings: Dict[str, Dict] = {}

# File path for persistent storage
_SETTINGS_FILE = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "project_settings.json")


def _load_project_settings():
    """Load project settings from file."""
    global _project_settings
    try:
        if os.path.exists(_SETTINGS_FILE):
            with open(_SETTINGS_FILE, "r") as f:
                _project_settings = json.load(f)
    except Exception as e:
        print(f"Error loading project settings: {e}")
        _project_settings = {}


def _save_project_settings():
    """Save project settings to file."""
    try:
        os.makedirs(os.path.dirname(_SETTINGS_FILE), exist_ok=True)
        with open(_SETTINGS_FILE, "w") as f:
            json.dump(_project_settings, f, indent=2)
    except Exception as e:
        print(f"Error saving project settings: {e}")


def get_project_tone(project_id: str) -> str:
    """Get tone mode for a project. Returns 'casual' if not set."""
    if not _project_settings:
        _load_project_settings()
    return _project_settings.get(project_id, {}).get("tone_mode", "casual")


def set_project_tone(project_id: str, tone_mode: str) -> bool:
    """
    Set tone mode for a project.

    Args:
        project_id: Project identifier
        tone_mode: One of 'casual', 'neutral', 'professional'

    Returns:
        True if successful, False if invalid tone_mode
    """
    valid_tones = ["casual", "neutral", "professional"]
    if tone_mode not in valid_tones:
        return False

    if not _project_settings:
        _load_project_settings()

    if project_id not in _project_settings:
        _project_settings[project_id] = {}

    _project_settings[project_id]["tone_mode"] = tone_mode
    _save_project_settings()
    return True


# Load settings on module import
_load_project_settings()


# =============================================================================
# SMART DUPLICATE RESPONSES (Sassy + Contextual)
# =============================================================================

def get_smart_duplicate_response(topic: str, repeat_count: int) -> Optional[str]:
    """
    Generate sassy, contextual duplicate response based on topic and repeat count.
    Escalates: friendly → sassy → dramatic → soft final → silent
    Returns None if bot should stay silent.
    """
    topic_str = topic if topic else "that"

    if repeat_count == 1:
        # Level 1: Friendly nudge
        responses = [
            f"just covered {topic_str} above 👆",
            f"answered {topic_str} a sec ago, scroll up a bit",
            f"check above ser - just went over {topic_str}",
            f"^ {topic_str} is right there fam",
        ]
    elif repeat_count == 2:
        # Level 2: Sassy but helpful
        responses = [
            f"bro we just talked about {topic_str} 😅",
            f"i know you saw my answer on {topic_str} 👀",
            f"deja vu... {topic_str} again? same answer as before",
            f"still no new info on {topic_str}, nothing changed yet",
            f"{topic_str} answer hasn't moved ser, check above",
        ]
    elif repeat_count == 3:
        # Level 3: Dramatic but informative
        responses = [
            f"you're stressing me out with {topic_str} rn 😭 answer's still the same",
            f"ser pls, {topic_str} hasn't changed in the last 2 mins",
            f"my brother in christ, {topic_str} is answered above 🙏",
            f"asking about {topic_str} again won't change my answer lol",
            f"the {topic_str} answer is still up there, i promise",
        ]
    elif repeat_count == 4:
        # Level 4: Final warning before silent mode
        responses = [
            f"still no updates on {topic_str} - gonna go quiet on this one now 🤐",
            f"same answer on {topic_str}, i'll stop repeating myself after this 🙏",
            f"{topic_str} hasn't changed - last reminder, going silent on this for a bit",
            f"nothing new on {topic_str} yet - i'll chill on responding to this now",
            f"answered {topic_str} already, gonna mute myself on this topic for now 🔇",
        ]
    else:
        # Level 5+: Silent mode (resets after 10 mins)
        # PATCH 3: Changed from 6 to 4 for earlier silent mode
        return None

    return random.choice(responses)


def normalize_question(text: str) -> str:
    """Normalize question for comparison."""
    import re
    # Lowercase
    text = text.lower().strip()
    # Remove punctuation
    text = re.sub(r'[^\w\s]', '', text)
    # Remove extra whitespace
    text = re.sub(r'\s+', ' ', text)
    # Remove common filler words
    fillers = ['please', 'pls', 'can you', 'could you', 'hey', 'hi', 'hello', 'yo', 'the', 'a', 'an']
    for filler in fillers:
        text = re.sub(rf'\b{filler}\b', '', text)
    return text.strip()


def extract_intent(text: str) -> Optional[str]:
    """
    Extract the primary intent from a question.
    Returns the intent category or None if no clear intent.
    """
    text_lower = text.lower()

    for intent, keywords in INTENT_KEYWORDS.items():
        for keyword in keywords:
            if keyword in text_lower:
                return intent

    return None


def extract_intents(text: str) -> List[str]:
    """
    Extract ALL intents from a question (for multi-topic detection).
    Returns list of intent categories found.

    PATCH 1: Used to detect multi-topic questions for formatting.
    """
    text_lower = text.lower()
    found_intents = []

    for intent, keywords in INTENT_KEYWORDS.items():
        for keyword in keywords:
            if keyword in text_lower:
                if intent not in found_intents:
                    found_intents.append(intent)
                break  # Found this intent, move to next

    return found_intents


def is_multi_topic(text: str) -> bool:
    """
    Check if a question contains multiple topics.
    Returns True if 2+ distinct intents detected.
    """
    return len(extract_intents(text)) >= 2


def simple_similarity(q1: str, q2: str) -> float:
    """Simple word-based similarity score."""
    words1 = set(normalize_question(q1).split())
    words2 = set(normalize_question(q2).split())

    if not words1 or not words2:
        return 0.0

    intersection = words1 & words2
    union = words1 | words2

    return len(intersection) / len(union) if union else 0.0


def find_cached_answer(question: str, project_id: str) -> Optional[Dict]:
    """
    Check if a similar question was recently answered.

    Returns:
        Dict with {answer, message_ref, user_id, timestamp} if found, None otherwise
    """
    import time

    if project_id not in _question_cache:
        return None

    now = time.time()
    normalized_q = normalize_question(question)

    # Clean expired entries
    _question_cache[project_id] = [
        entry for entry in _question_cache[project_id]
        if now - entry['timestamp'] < CACHE_EXPIRY
    ]

    # Find similar question
    for entry in reversed(_question_cache[project_id]):  # Check recent first
        if simple_similarity(question, entry['question']) >= SIMILARITY_THRESHOLD:
            return entry

    return None


def cache_answer(question: str, answer: str, project_id: str,
                 message_ref: str, user_id: str):
    """
    Cache a Q&A for duplicate detection.

    Args:
        question: The original question
        answer: The answer given
        project_id: Project/server ID
        message_ref: Platform-specific message reference (link or ID)
        user_id: Who asked the question
    """
    import time

    if project_id not in _question_cache:
        _question_cache[project_id] = []

    entry = {
        'question': question,
        'answer': answer,
        'message_ref': message_ref,
        'user_id': user_id,
        'timestamp': time.time()
    }

    _question_cache[project_id].append(entry)

    # Trim to max size
    if len(_question_cache[project_id]) > CACHE_SIZE:
        _question_cache[project_id] = _question_cache[project_id][-CACHE_SIZE:]


def clear_cache(project_id: str = None):
    """Clear question cache for a project or all."""
    global _question_cache
    if project_id:
        _question_cache.pop(project_id, None)
    else:
        _question_cache = {}


def get_repeat_count(cache_key: str) -> int:
    """
    Get and increment repeat count for a cache key (channel:topic).
    Auto-resets after REPEAT_RESET_WINDOW seconds.
    """
    now = time.time()

    # Check if we should reset
    last_time = _repeat_timestamps.get(cache_key, 0)
    if now - last_time > REPEAT_RESET_WINDOW:
        _repeat_counts[cache_key] = 0

    # Increment and return
    _repeat_counts[cache_key] = _repeat_counts.get(cache_key, 0) + 1
    _repeat_timestamps[cache_key] = now

    return _repeat_counts[cache_key]


def reset_repeat_count(cache_key: str = None):
    """Reset repeat count for a key or all keys."""
    global _repeat_counts, _repeat_timestamps
    if cache_key:
        _repeat_counts.pop(cache_key, None)
        _repeat_timestamps.pop(cache_key, None)
    else:
        _repeat_counts = {}
        _repeat_timestamps = {}


def extract_topic(text: str) -> str:
    """
    Extract the main topic from a question for contextual responses.
    Returns a short topic string.
    """
    text_lower = text.lower().strip()

    # Check known intents first
    for intent, keywords in INTENT_KEYWORDS.items():
        for keyword in keywords:
            if keyword in text_lower:
                # Return readable topic name
                topic_names = {
                    'airdrop': 'the airdrop',
                    'snapshot': 'the snapshot',
                    'tge': 'TGE',
                    'listing': 'listings',
                    'staking': 'staking',
                    'tokenomics': 'tokenomics',
                    'roadmap': 'the roadmap',
                    'wallet': 'wallet stuff',
                    'price': 'price',
                    'eligibility': 'eligibility',
                }
                return topic_names.get(intent, intent)

    # Fallback: extract key nouns (simple approach)
    # Remove question words and common filler
    remove_words = ['what', 'when', 'where', 'how', 'why', 'is', 'are', 'the', 'a', 'an',
                    'do', 'does', 'can', 'will', 'wen', 'ser', 'pls', 'please', '?']
    words = text_lower.split()
    topic_words = [w for w in words if w not in remove_words and len(w) > 2]

    if topic_words:
        return ' '.join(topic_words[:2])  # Max 2 words

    return "that"


def check_cooldown(user_id: str) -> tuple[bool, int]:
    """
    Check if user is on cooldown.

    Returns:
        (is_allowed, seconds_remaining)
    """
    now = time.time()
    last_time = _user_cooldowns.get(user_id, 0)
    elapsed = now - last_time

    if elapsed < USER_COOLDOWN:
        remaining = int(USER_COOLDOWN - elapsed)
        return False, remaining

    return True, 0


def record_question(user_id: str):
    """Record that user asked a question (for cooldown tracking)."""
    _user_cooldowns[user_id] = time.time()


def reset_cooldown(user_id: str):
    """Reset cooldown for a user (e.g., after error)."""
    if user_id in _user_cooldowns:
        del _user_cooldowns[user_id]


# =============================================================================
# MESSAGE ANALYSIS
# =============================================================================

def should_ignore(text: str) -> bool:
    """
    Check if message should be ignored (greetings, reactions, etc.)

    Returns True if bot should NOT respond.
    """
    text_clean = text.strip().lower()

    # Too short
    if len(text_clean) < 2:
        return True

    # Exact match with ignore patterns
    if text_clean in [p.lower() for p in IGNORE_PATTERNS]:
        return True

    # Just emojis (no real text)
    import re
    text_no_emoji = re.sub(r'[\U0001F600-\U0001F64F\U0001F300-\U0001F5FF\U0001F680-\U0001F6FF\U0001F1E0-\U0001F1FF\U00002702-\U000027B0\U0001F900-\U0001F9FF\U0001FA00-\U0001FA6F\U0001FA70-\U0001FAFF\U00002600-\U000026FF]', '', text_clean)
    if len(text_no_emoji.strip()) < 2:
        return True

    # Starts with common ignore patterns
    ignore_starts = ['lol', 'haha', 'nice', 'cool', 'wow', 'thanks', 'ty ', 'thx']
    if any(text_clean.startswith(p) for p in ignore_starts):
        # But allow if it's actually a question
        if not is_question(text):
            return True

    return False


def is_question(text: str) -> bool:
    """
    Check if message looks like a question that deserves an answer.

    Returns True if bot SHOULD respond.
    """
    text_lower = text.lower().strip()

    # Has question mark - definitely a question
    if '?' in text:
        return True

    # Check for question signals
    for signal in QUESTION_SIGNALS:
        if signal in text_lower:
            return True

    # Long enough message that might be a question without ?
    # (some people don't use punctuation)
    words = text_lower.split()
    if len(words) >= 4:
        # Starts with question words
        question_starters = ['how', 'what', 'where', 'when', 'why', 'can', 'does', 'is', 'are', 'do', 'will', 'should']
        if words[0] in question_starters:
            return True

    return False


def is_greeting(text: str) -> bool:
    """Check if message is just a greeting."""
    greetings = ['gm', 'gn', 'hey', 'hi', 'hello', 'yo', 'sup', 'good morning', 'good night']
    text_clean = text.strip().lower()
    return text_clean in greetings or any(text_clean.startswith(g + ' ') for g in greetings[:5])


# =============================================================================
# HUMAN-LIKE DELAYS
# =============================================================================

async def human_typing_delay():
    """Add a random delay to simulate human typing/thinking."""
    delay = random.uniform(TYPING_DELAY_MIN, TYPING_DELAY_MAX)
    await asyncio.sleep(delay)


def get_random_delay() -> float:
    """Get a random delay value (for non-async contexts)."""
    return random.uniform(TYPING_DELAY_MIN, TYPING_DELAY_MAX)


# =============================================================================
# RESPONSE VARIATIONS
# =============================================================================

# Casual responses when bot doesn't know
UNSURE_RESPONSES = [
    "hmm not 100% sure on that one - might be worth asking in the main chat",
    "that's not really covered in the docs i have, maybe check with the team?",
    "honestly not finding much on that - could be a question for the core team",
    "don't have a clear answer for that one, sorry! team might know better",
]

# Responses when docs aren't loaded
NO_DOCS_RESPONSES = [
    "hey! i don't have any docs loaded yet for this server - an admin needs to add some first",
    "no docs loaded here yet! once an admin adds some, i can help answer questions",
    "looks like docs haven't been set up yet - ping an admin to load them up",
]

# Casual closings (randomly appended sometimes)
CASUAL_CLOSINGS = [
    "",  # No closing most of the time
    "",
    "",
    " 👍",
    " hope that helps!",
    " lmk if that makes sense",
]


def get_unsure_response() -> str:
    """Get a random 'I don't know' response."""
    return random.choice(UNSURE_RESPONSES)


def get_no_docs_response() -> str:
    """Get a random 'no docs loaded' response."""
    return random.choice(NO_DOCS_RESPONSES)


def maybe_add_closing(response: str) -> str:
    """Maybe add a casual closing to response (30% chance)."""
    if random.random() < 0.3:
        closing = random.choice([c for c in CASUAL_CLOSINGS if c])  # Non-empty
        if closing and not response.rstrip().endswith(('!', '?', '👍')):
            return response.rstrip() + closing
    return response
