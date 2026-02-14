# DocBot

AI-powered community support bot for crypto/web3 projects. Answers questions 24/7 based on your project documentation.

![Python](https://img.shields.io/badge/Python-3.11+-blue)
![License](https://img.shields.io/badge/License-MIT-green)
![Platforms](https://img.shields.io/badge/Platforms-Telegram%20%7C%20Discord-purple)

> Part of the **ChainPilot** suite - AI agents for Web3 community management.

## What It Does

DocBot ingests your project documentation (docs, FAQ, whitepaper) and answers community questions automatically on Telegram and Discord.

- **One Brain, Two Platforms** - Same AI powers both Telegram and Discord
- **Multi-Tenant** - Each server/group has isolated docs (SaaS-ready)
- **Context-Aware** - Uses RAG to find relevant documentation
- **Honest** - Says "I don't know" instead of hallucinating
- **Fast** - Powered by Groq's lightning-fast inference (free tier!)

## Features

- Load documents from files (`.txt`, `.md`, `.pdf`) or URLs
- Multi-tenant: each Discord server / Telegram group has isolated knowledge
- Discord slash commands (`/ask`, `/status`, `/load_url`)
- Telegram commands (`/ask`, `/status`, `/load_text`)
- File upload support - just drop a doc and it's ingested
- Easy to switch LLM providers (Groq, OpenAI, Claude, etc.)

## Quick Start

### 1. Clone and install

```bash
git clone https://github.com/yourusername/docbot.git
cd docbot
pip install -r requirements.txt
```

### 2. Set up environment variables

Create a `.env` file:

```env
GROQ_API_KEY=your_groq_api_key
TELEGRAM_BOT_TOKEN=your_telegram_bot_token
DISCORD_BOT_TOKEN=your_discord_bot_token
```

Get your keys:
- **Groq**: [console.groq.com](https://console.groq.com) (free)
- **Telegram**: [@BotFather](https://t.me/botfather)
- **Discord**: [Discord Developer Portal](https://discord.com/developers/applications)

### 3. Run locally

```bash
# Test the AI brain
python main.py test

# Run Telegram bot
python main.py telegram

# Run Discord bot
python main.py discord

# Run both (production)
python run_bots.py
```

## Commands

### Discord (Slash Commands)

| Command | Description |
|---------|-------------|
| `/ask <question>` | Ask DocBot a question |
| `/status` | Check bot status and doc count |
| `/help` | Show available commands |
| `/docs_info` | Show loaded docs info (Admin) |
| `/load_url <url>` | Load docs from URL (Admin) |
| `/load_text <text>` | Add text to knowledge (Admin) |
| `/clear_docs` | Clear all docs (Admin) |

You can also @mention the bot with a question!

### Telegram

| Command | Description |
|---------|-------------|
| `/ask <question>` | Ask a question |
| `/status` | Check bot status |
| `/docs_info` | Show loaded docs |
| `/load_text <text>` | Add text (Admin) |
| `/load_url <url>` | Load from URL (Admin) |
| `/clear_docs` | Clear docs (Admin) |

Or just type your question directly!

**File Upload**: Drop a `.txt`, `.md`, or `.pdf` file to add it to the knowledge base.

## Deploy to Railway

### 1. Push to GitHub

```bash
git add .
git commit -m "Ready for deployment"
git push origin main
```

### 2. Deploy on Railway

1. Go to [railway.app](https://railway.app)
2. Click "New Project" → "Deploy from GitHub repo"
3. Select your DocBot repo
4. Add environment variables:
   - `GROQ_API_KEY`
   - `TELEGRAM_BOT_TOKEN`
   - `DISCORD_BOT_TOKEN`
5. Deploy!

Railway will automatically use the `Procfile` to run both bots.

### Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `GROQ_API_KEY` | Yes | Get from console.groq.com |
| `TELEGRAM_BOT_TOKEN` | No* | Get from @BotFather |
| `DISCORD_BOT_TOKEN` | No* | Get from Discord Dev Portal |

*At least one bot token is required.

## Project Structure

```
docbot/
├── main.py              # CLI entry point
├── run_bots.py          # Production runner (both bots)
├── config.py            # Configuration
├── Procfile             # Railway deployment
├── railway.json         # Railway config
│
├── brain/
│   ├── ingester.py      # Document loading & chunking
│   ├── vectorstore.py   # Vector search (multi-tenant)
│   └── answerer.py      # LLM response generation
│
├── connectors/
│   ├── telegram_bot.py  # Telegram integration
│   └── discord_bot.py   # Discord integration
│
└── data/
    └── docs/            # Local test documents
```

## Configuration

Edit `config.py` to customize:

```python
# Switch LLM provider
LLM_MODEL = "groq/llama-3.3-70b-versatile"  # Free, fast
# LLM_MODEL = "gpt-4o-mini"                  # OpenAI
# LLM_MODEL = "claude-3-haiku-20240307"      # Anthropic

# Chunking settings
CHUNK_SIZE = 500
CHUNK_OVERLAP = 50

# Search results per query
TOP_K_RESULTS = 3

# Confidence threshold (0-1)
CONFIDENCE_THRESHOLD = 0.3
```

## Multi-Tenant Architecture

Each Discord server and Telegram group gets **isolated documentation**:

- Server A's docs are only searchable by Server A members
- Server B can have completely different docs
- Great for SaaS: one deployment serves many projects

## Roadmap

- [x] Multi-tenant support
- [x] Discord slash commands
- [x] File upload ingestion
- [x] URL scraping
- [ ] Web dashboard
- [ ] Analytics (most asked questions)
- [ ] Real embeddings (sentence-transformers)
- [ ] White-label bot names

## Part of ChainPilot

DocBot is the first agent in the **ChainPilot** suite:

1. **DocBot** - Documentation Q&A (this repo)
2. **AnnounceBot** - Content generation (coming soon)
3. **ModBot** - Spam/scam detection
4. **OnboardBot** - New member guidance
5. **GovernanceBot** - DAO tools
6. **AnalyticsBot** - Community metrics
7. **AlphaBot** - News curation

## License

MIT License - use freely for your project!

---

**Need help?** Open an issue or DM for custom setup!
