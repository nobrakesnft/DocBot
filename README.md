# DocBot

AI-powered community support bot for crypto/web3 projects. Answers questions 24/7 based on your project documentation.

![Python](https://img.shields.io/badge/Python-3.11+-blue)
![License](https://img.shields.io/badge/License-MIT-green)
![Platforms](https://img.shields.io/badge/Platforms-Telegram%20%7C%20Discord-purple)

## What It Does

DocBot ingests your project documentation (docs, FAQ, whitepaper) and answers community questions automatically on Telegram and Discord.

- **One Brain, Two Platforms** - Same AI logic powers both Telegram and Discord bots
- **Context-Aware** - Uses RAG (Retrieval Augmented Generation) to find relevant docs
- **Honest** - Says "I don't know" when unsure instead of hallucinating
- **Fast** - Powered by Groq's lightning-fast LLM inference

## Features

- Load documents from files (`.txt`, `.md`, `.pdf`) or URLs
- Vector search to find relevant documentation chunks
- LLM-powered answer generation
- Telegram bot with `/ask`, `/status`, `/reload` commands
- Discord bot with `!ask`, `!status`, `!docbot` commands
- Easy to switch between LLM providers (Groq, OpenAI, etc.)

## Quick Start

### 1. Clone the repo

```bash
git clone https://github.com/yourusername/docbot.git
cd docbot
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Set up environment variables

Create a `.env` file:

```env
GROQ_API_KEY=your_groq_api_key
TELEGRAM_BOT_TOKEN=your_telegram_bot_token
DISCORD_BOT_TOKEN=your_discord_bot_token
```

Get your keys:
- **Groq**: [console.groq.com](https://console.groq.com) (free)
- **Telegram**: [@BotFather](https://t.me/botfather) on Telegram
- **Discord**: [Discord Developer Portal](https://discord.com/developers/applications)

### 4. Add your documents

Put your project docs in `data/docs/`:

```
data/docs/
├── whitepaper.md
├── faq.txt
└── getting-started.pdf
```

### 5. Load documents

```bash
python main.py ingest
```

### 6. Run the bots

```bash
# Telegram
python main.py telegram

# Discord
python main.py discord

# Test the AI brain
python main.py test
```

## Commands

### Telegram
| Command | Description |
|---------|-------------|
| `/start` | Welcome message |
| `/ask <question>` | Ask a question |
| `/status` | Check bot status |
| `/reload` | Reload documents (admin) |

Or just type your question directly!

### Discord
| Command | Description |
|---------|-------------|
| `!ask <question>` | Ask a question |
| `!docbot <question>` | Same as !ask |
| `!status` | Check bot status |
| `!help_docbot` | Show help |

## Project Structure

```
docbot/
├── main.py              # Entry point
├── config.py            # Configuration
├── requirements.txt     # Dependencies
├── .env                 # API keys (not committed)
│
├── brain/
│   ├── ingester.py      # Document loading & chunking
│   ├── vectorstore.py   # Vector search
│   └── answerer.py      # LLM response generation
│
├── connectors/
│   ├── telegram_bot.py  # Telegram integration
│   └── discord_bot.py   # Discord integration
│
└── data/
    └── docs/            # Your documentation files
```

## Configuration

Edit `config.py` to customize:

```python
# Switch LLM provider
LLM_MODEL = "groq/llama-3.3-70b-versatile"  # Free
# LLM_MODEL = "gpt-4o-mini"                  # OpenAI (paid)

# Adjust chunking
CHUNK_SIZE = 500
CHUNK_OVERLAP = 50

# Search results
TOP_K_RESULTS = 3
```

## Tech Stack

- **Python 3.11+**
- **LiteLLM** - Universal LLM interface
- **Groq** - Fast, free LLM inference
- **python-telegram-bot** - Telegram integration
- **discord.py** - Discord integration

## Use Cases

- Crypto/DeFi projects needing 24/7 community support
- DAOs with documentation that members frequently ask about
- Any project wanting to reduce repetitive community questions

## Roadmap

- [ ] Web dashboard for managing docs
- [ ] Analytics (most asked questions)
- [ ] Multi-language support
- [ ] Slack integration

## License

MIT License - feel free to use for your project!

## Author

Built with AI assistance. Powered by [Groq](https://groq.com).

---

**Want this for your project?** DM me for setup help or custom features!
