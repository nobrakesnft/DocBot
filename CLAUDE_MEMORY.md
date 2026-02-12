# DocBot - Claude Session Memory

> **IMPORTANT**: Read this file at the start of EVERY session.
> User will say: "Read the memory file" or "Let's continue DocBot"
> This file is the single source of truth for project status.

---

## Project Location

```
C:\Users\HP OWNER\vibecoding\
├── DocBot\          ← THIS PROJECT
│   ├── CLAUDE_MEMORY.md
│   └── DocBot_PRD.md
│
└── DealPact\        ← User's previous bot (reference)
    └── bot\
```

---

## Quick Context (Read First)

**Project**: DocBot - AI community support bot for crypto/web3 projects
**User**: Web3 native, community manager, built DealPact (Telegram bot), learning to code via vibe coding
**Goal**: Build DocBot to (1) get hired as AI/bot developer, (2) sell as SaaS $99-299/mo
**Base Path**: `C:\Users\HP OWNER\vibecoding\DocBot\`

**Tech Stack**:
- Python 3.11+
- LLM: Groq (free) via LiteLLM (can switch to OpenAI anytime)
- Vector DB: ChromaDB (local, free)
- Platforms: Telegram + Discord (shared AI brain)
- Hosting: Railway (free tier)

---

## Current Status

| Component | Status | Notes |
|-----------|--------|-------|
| PRD | ✅ Done | `DocBot_PRD.md` |
| Project Structure | 🔴 Not started | |
| Config/Environment | 🔴 Not started | Need Groq API key |
| Document Ingester | 🔴 Not started | |
| Vector Store | 🔴 Not started | |
| LLM Answerer | 🔴 Not started | |
| Telegram Bot | 🔴 Not started | |
| Discord Bot | 🔴 Not started | |
| GitHub Repo | 🔴 Not started | |
| README | 🔴 Not started | |
| Pitch Materials | 🔴 Not started | |
| First Beta User | 🔴 Not started | |

---

## Build Order (Follow This Sequence)

```
Phase 1: Foundation
├── 1. Create project structure
├── 2. Set up config.py and .env
├── 3. Get Groq API key
└── 4. Test LLM connection

Phase 2: Brain
├── 5. Build document ingester (load, chunk, embed)
├── 6. Set up ChromaDB vector store
├── 7. Build search function
└── 8. Build LLM answerer

Phase 3: Connectors
├── 9. Build Telegram bot
├── 10. Build Discord bot
└── 11. Test both with real docs

Phase 4: Ship
├── 12. Create GitHub repo
├── 13. Write README
├── 14. Deploy to Railway
└── 15. Create pitch materials
```

**Currently On**: Step 1 - Create project structure

---

## File Structure (Target)

```
DocBot/
├── CLAUDE_MEMORY.md        # This file (session memory)
├── DocBot_PRD.md           # Product requirements
├── README.md               # GitHub readme (create later)
├── requirements.txt        # Python dependencies
├── .env                    # API keys (DO NOT commit)
├── .gitignore              # Ignore .env, __pycache__, etc.
├── config.py               # Configuration loader
├── main.py                 # Entry point
│
├── brain/
│   ├── __init__.py
│   ├── ingester.py         # Load and chunk documents
│   ├── vectorstore.py      # ChromaDB operations
│   └── answerer.py         # LLM response generation
│
├── connectors/
│   ├── __init__.py
│   ├── telegram_bot.py     # Telegram integration
│   └── discord_bot.py      # Discord integration
│
├── data/
│   ├── docs/               # Sample docs for testing
│   └── chroma_db/          # Vector database storage
│
└── tests/
    └── test_brain.py       # Basic tests
```

---

## Session Log

### Session 1 - February 12, 2026
**What happened**:
- Brainstormed project ideas, landed on DocBot
- Created full PRD (science-fair level)
- Designed architecture: one brain, two platform connectors
- Decided on tech stack: Python, Groq, ChromaDB, LiteLLM
- User created `vibecoding` folder to organize all projects
- Moved DocBot into `C:\Users\HP OWNER\vibecoding\DocBot\`
- DealPact (previous project) also in vibecoding folder
- Created this memory file

**Decisions made**:
- Use Groq (free) for LLM, switch to OpenAI later via LiteLLM
- Support both Telegram AND Discord from day 1
- Pricing: $99 / $199 / $299 tiers
- Target: Free beta users first, then monetize
- Dropped Web3 Career Roadmap, focusing only on DocBot

**User needs to do before next session**:
- [ ] Get Groq API key from console.groq.com
- [ ] Have GitHub account ready
- [ ] (Optional) Think of a project to test with

**Next session starts with**:
- Create project structure (folders, files)
- Set up config.py and .env
- Install dependencies
- Test Groq connection

---

## Technical Decisions Log

| Decision | Choice | Reason |
|----------|--------|--------|
| Language | Python | Best for AI, good bot libraries |
| LLM Provider | Groq (free) | $0 cost, can switch later |
| LLM Wrapper | LiteLLM | Easy switching between providers |
| Vector DB | ChromaDB | Free, local, simple |
| Telegram Lib | python-telegram-bot | Mature, well-documented |
| Discord Lib | discord.py | Industry standard |
| Hosting | Railway | Free tier, simple deploy |

---

## User Context

**Skills**:
- Community management (strong)
- Telegram bots (built DealPact)
- Vibe coding with AI (learning)
- Web3 native (understands the space)

**Situation**:
- Needs income
- Looking for web3 job
- DocBot serves dual purpose: portfolio + SaaS income

**Communication style**:
- Explain everything step by step
- User is learning, not a senior developer
- Celebrate wins, keep momentum up

---

## Blockers / Open Questions

| Issue | Status | Resolution |
|-------|--------|------------|
| Groq API key | Pending | User needs to sign up |
| Test documents | Pending | Need sample project docs |
| GitHub account | Unknown | Check with user |

---

## How To Use This File

**For Claude (me)**:
1. Read this file first every session
2. Check "Current Status" table
3. Look at "Currently On" step
4. Read latest session log
5. Continue from where we left off

**For User**:
1. Start session with: "Read the memory file" or "Let's continue DocBot"
2. After session: I'll update this file
3. If stuck: Add to "Blockers" section

---

## Quick Commands

When user says... | I should...
------------------|------------
"Read the memory file" | Read this file, summarize status, continue
"Let's continue DocBot" | Same as above
"Update memory" | Add session log, update status
"What's next?" | Check build order, tell them next step
"I got the API key" | Move to testing LLM connection

---

*Last updated: February 12, 2026*
