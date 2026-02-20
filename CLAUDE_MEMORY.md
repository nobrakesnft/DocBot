# DocBot - Claude Session Memory

> **IMPORTANT**: Read this file at the start of EVERY session.
> This file is the single source of truth for project status.

---

## Quick Context

**Project**: DocBot - AI community support bot for Web3 projects
**Part of**: ChainPilot Suite (see `C:\Users\HP OWNER\ChainPilot\docs\`)
**User**: Web3 native, community manager, learning via vibe coding
**Goal**: Build DocBot → Deploy → Get users → Then build AnnounceBot

**Base Path**: `C:\Users\HP OWNER\Vibecoding\DocBot\`

---

## Current Status (February 2026)

| Component | Status | Notes |
|-----------|--------|-------|
| PRD | Done | `DocBot_PRD.md` |
| Project Structure | Done | All files created |
| Config/Environment | Done | `.env` with Groq key |
| Document Ingester | Done | `brain/ingester.py` |
| Vector Store | Done | `brain/vectorstore.py` (simple embeddings) |
| LLM Answerer | Done | `brain/answerer.py` - human-like responses |
| Telegram Bot | Done | `connectors/telegram_bot.py` - smart detection |
| Discord Bot | Done | `connectors/discord_bot.py` - plain text replies |
| Multi-tenant | Done | Each server/group isolated |
| Human-like UX | Done | Question detection, rate limiting, casual tone |
| Shared Bot Utils | Done | `connectors/bot_utils.py` |
| **Deployment** | **NOT DONE** | Need Railway setup |
| **Real embeddings** | **NOT DONE** | Using simple hash (works for now) |
| **Beta testing** | **NOT DONE** | Need real project docs |

---

## ChainPilot Vision

DocBot is the **first agent** in ChainPilot - a Web3 Community Copilot Suite.

Full suite (build order):
1. **DocBot** ← YOU ARE HERE
2. AnnounceBot - content generation
3. ModBot - spam/scam detection
4. OnboardBot - new member guidance
5. GovernanceBot - DAO tools
6. AnalyticsBot - metrics
7. AlphaBot - news curation

See: `C:\Users\HP OWNER\ChainPilot\docs\CHAINPILOT_PRD.md`

---

## What's Working

```
python main.py test      # Test the brain - WORKS
python main.py ingest    # Load docs - WORKS
python main.py telegram  # Run Telegram bot - WORKS (needs token)
python main.py discord   # Run Discord bot - WORKS (needs token)
```

Features complete:
- RAG pipeline (question → search → LLM answer)
- Multi-tenant (each Discord server/Telegram group has isolated docs)
- File upload (.txt, .md, .pdf)
- URL loading
- Admin commands (/load_text, /load_url, /clear_docs, /docs_info)
- User commands (/ask, /status, @mention)

---

## What Needs to Be Done

### Priority 1: Deployment
- [ ] Add `Procfile` for Railway
- [ ] Add `railway.json` config
- [ ] Test deployment
- [ ] Set up environment variables on Railway

### Priority 2: Embeddings Upgrade (Optional but recommended)
Current: Simple hash-based embeddings (fast but less accurate)
Upgrade to: Sentence-transformers or OpenAI embeddings

### Priority 3: Beta Testing
- [ ] Find 1-2 Web3 projects to test with
- [ ] Load their real docs
- [ ] Gather feedback

---

## Tech Stack

| Component | Technology |
|-----------|------------|
| Language | Python 3.11+ |
| LLM | Groq (free) via LiteLLM |
| Vector DB | Custom (pickle-based, simple embeddings) |
| Telegram | python-telegram-bot |
| Discord | discord.py |
| Hosting | Railway (target) |

---

## File Structure

```
DocBot/
├── CLAUDE_MEMORY.md     # This file
├── DocBot_PRD.md        # Product requirements
├── README.md            # Setup guide
├── requirements.txt     # Dependencies
├── .env                 # API keys (not in git)
├── .gitignore
├── config.py            # Configuration
├── main.py              # Entry point
│
├── brain/
│   ├── __init__.py
│   ├── ingester.py      # Load and chunk docs
│   ├── vectorstore.py   # Vector storage + search
│   └── answerer.py      # LLM response generation
│
├── connectors/
│   ├── __init__.py
│   ├── bot_utils.py     # Shared utilities (rate limit, question detection)
│   ├── telegram_bot.py  # Telegram integration
│   └── discord_bot.py   # Discord integration
│
└── data/
    ├── docs/            # Sample docs
    ├── temp/            # Temp file storage
    └── chroma_db/       # Vector DB storage
```

---

## Session Log

### Session 4 - February 15, 2026
**What happened**:
- Major UX overhaul to make bot feel human, not bot-like
- Created shared `bot_utils.py` with common logic for both platforms
- Updated system prompt to be casual and human-like
- Removed embed replies on Discord - now uses plain text
- Added question detection (only responds to actual questions)
- Added rate limiting (15s cooldown per user)
- Added ignore patterns (gm, thanks, lol, etc. don't trigger responses)
- Added human-like typing delays
- Removed sources from default responses
- Raised LLM temperature to 0.7 for more natural variation
- Both Discord and Telegram bots now share same behavior

**Files changed**:
- `connectors/bot_utils.py` (NEW) - shared utilities
- `config.py` - new system prompt, temperature 0.7
- `brain/answerer.py` - random responses, no sources by default
- `connectors/discord_bot.py` - plain text, reply threading, smart detection
- `connectors/telegram_bot.py` - smart response logic, rate limiting
- `connectors/__init__.py` - added bot_utils export

**Key behavior changes**:
- Bot only responds to questions (not "gm", "thanks", etc.)
- Replies to message instead of new message (Discord)
- Short, casual responses like a community member
- 15 second cooldown between questions per user
- Random variation in error messages and closings

**Next steps**:
- Deploy to Railway and test live
- Monitor community feedback on bot personality
- Fine-tune ignore patterns based on real usage

### Session 3 - February 14, 2026
**What happened**:
- Pivoted DocBot into ChainPilot suite vision
- Created ChainPilot PRD with 7 agents
- Reviewed existing DocBot code - it's 80% complete!
- Created integration plan for ChainPilot monorepo
- Discovered IdeaRalph MCP is broken (prompt-only)

**Decisions made**:
- Build DocBot first, deploy, get users
- Then add AnnounceBot
- Migrate to ChainPilot monorepo when we have 2+ bots
- Keep DocBot standalone for now

**Next steps**:
- Add Railway deployment files
- Optionally upgrade embeddings
- Deploy and test

### Session 2 - February 13, 2026
**What happened**:
- Built Telegram bot connector
- Built Discord bot connector
- Added multi-tenant support
- Added file upload and URL loading

### Session 1 - February 12, 2026
**What happened**:
- Created PRD
- Built brain (ingester, vectorstore, answerer)
- Set up project structure

---

## Quick Commands

| Command | What it does |
|---------|--------------|
| `python main.py test` | Test the AI brain |
| `python main.py ingest` | Load docs from data/docs/ |
| `python main.py telegram` | Run Telegram bot |
| `python main.py discord` | Run Discord bot |

---

*Last updated: February 15, 2026*
