# DocBot - Product Requirements Document

> **Version**: 1.0
> **Author**: [Your Name]
> **Date**: February 12, 2026
> **Status**: MVP Planning

---

## 1. Executive Summary

DocBot is an AI-powered community support bot that helps crypto/web3 projects provide 24/7 automated support on Discord and Telegram. The bot ingests project documentation (whitepapers, docs, FAQs) and uses AI to answer community questions instantly and accurately. Built by a community manager who understands the real questions users ask, DocBot targets small-to-mid crypto projects that need quality support but can't afford full-time community managers.

---

## 2. Problem Statement

### The Pain Points

| Problem | Evidence | Impact |
|---------|----------|--------|
| **Repetitive questions drain CMs** | 70%+ of community questions are the same (how to stake, how to buy, tokenomics, etc.) | CM burnout, slow responses |
| **No 24/7 coverage** | Projects have global communities but CMs sleep | Users leave, frustration builds |
| **Hiring is expensive** | Full-time CM costs $2,000-5,000/month | Small projects can't afford it |
| **Inconsistent answers** | Different CMs give different answers | Confusion, trust issues |
| **Knowledge scattered** | Docs in Notion, FAQ on website, updates in Discord | Hard to find answers |

### Current Solutions & Gaps

| Solution | What It Does | Gap |
|----------|--------------|-----|
| Human CMs | Answer questions manually | Expensive, not 24/7, inconsistent |
| Keyword bots | Reply to triggers like "!tokenomics" | Rigid, can't handle variations |
| General AI bots | ChatGPT wrappers | Not trained on project-specific info |
| Kapa.ai, Mendable | AI docs Q&A | Enterprise pricing, not crypto-native |

### Why Now?

1. **LLMs are accessible** - Quality AI is now affordable (Groq free, GPT-4o cheap)
2. **Crypto projects are scaling** - More users = more questions
3. **Community is competitive** - Good support = user retention
4. **AI acceptance** - Users now expect AI assistance

---

## 3. Target Users

### Primary Persona: "Small Project Pete"

| Attribute | Details |
|-----------|---------|
| **Role** | Founder or Community Lead at crypto project |
| **Team size** | 2-15 people |
| **Community size** | 500-20,000 members |
| **Budget** | $100-500/month for community tools |
| **Pain** | Drowning in questions, can't afford another CM |
| **Channels** | Telegram primary, Discord secondary |
| **Tech comfort** | Can copy-paste, not a developer |

### Secondary Persona: "DAO Diana"

| Attribute | Details |
|-----------|---------|
| **Role** | Community contributor / volunteer CM |
| **Organization** | DAO or decentralized project |
| **Pain** | Answering same questions daily, no compensation |
| **Need** | Automate 80% of questions so she can focus on important stuff |

### User Journey Map

```
Discovery
    │ "I'm spending 4 hours/day answering the same questions"
    │ Sees tweet/post about DocBot
    ▼
Evaluation
    │ "Can it actually answer questions correctly?"
    │ Tries demo, sees it knows project-specific stuff
    ▼
Onboarding
    │ "How hard is setup?"
    │ Uploads docs, bot learns in 5 minutes
    │ Adds bot to Telegram/Discord
    ▼
First Value
    │ Bot answers first question correctly
    │ "Holy shit it actually works"
    ▼
Habit
    │ Bot handles 50%+ of questions
    │ CM focuses on complex issues only
    ▼
Expansion
    │ "Can I get this for our other community too?"
    │ Upgrades plan, refers other projects
```

---

## 4. Solution Overview

### Core Value Proposition

**"24/7 community support that actually knows your project."**

DocBot answers questions like a knowledgeable team member, not a generic chatbot. It learns your specific docs, tokenomics, guides, and FAQs - then responds accurately on Telegram and Discord.

### Key Differentiators

| Us | Them |
|----|------|
| Crypto-native (understands the culture) | Generic enterprise tools |
| Built by a CM (knows real questions) | Built by devs who never moderated |
| Works on Telegram + Discord | Often one platform only |
| $99-299/month | $500-2000/month |
| Setup in 10 minutes | Days of configuration |
| Admits when it doesn't know | Hallucinator or silent |

---

## 5. Feature Requirements

### MVP Features (P0 - Must Have)

| Feature | Description | Acceptance Criteria |
|---------|-------------|---------------------|
| **Doc Ingestion** | Upload docs via URL, file, or paste text | Supports PDF, MD, TXT, URLs |
| **Vector Search** | Find relevant doc chunks for any question | Returns top 3 relevant chunks |
| **AI Answering** | Generate accurate answers from context | Uses Groq/OpenAI, cites sources |
| **Telegram Bot** | Listen and respond in Telegram groups | Works in groups, handles mentions |
| **Discord Bot** | Listen and respond in Discord channels | Responds to questions in designated channels |
| **"I Don't Know"** | Graceful fallback when unsure | Says "I'm not sure, please ask a mod" |
| **Admin Commands** | Basic controls for project owners | /reload docs, /status, /help |

### Phase 2 Features (P1 - After MVP)

| Feature | Description |
|---------|-------------|
| **Web Dashboard** | View questions, update docs, see analytics |
| **Unanswered Log** | Track questions bot couldn't answer |
| **Multi-language** | Auto-detect and respond in user's language |
| **Custom Personality** | Set bot tone (formal, casual, degen) |
| **Conversation Context** | Remember previous messages in thread |

### Nice-to-Haves (P2 - Future)

| Feature | Description |
|---------|-------------|
| **Auto-update docs** | Pull from Notion/GitBook automatically |
| **Sentiment analysis** | Alert team when users are frustrated |
| **Mod escalation** | Tag human mod for complex issues |
| **Analytics dashboard** | Top questions, response times, satisfaction |
| **Whitelabel** | Remove DocBot branding for premium clients |

---

## 6. User Stories

### Story 1: Project Owner Sets Up Bot
**As a** project owner
**I want to** add my docs and deploy the bot quickly
**So that** I can get 24/7 support running today

**Acceptance Criteria:**
- Can upload docs in under 5 minutes
- Bot is live in Telegram/Discord within 10 minutes
- No coding required

---

### Story 2: Community Member Asks Question
**As a** community member
**I want to** ask a question and get an instant answer
**So that** I don't have to wait hours for a CM

**Acceptance Criteria:**
- Response within 5 seconds
- Answer is relevant and accurate
- Sources cited when possible

---

### Story 3: Bot Handles Unknown Question
**As a** community member
**I want to** get help even when the bot doesn't know
**So that** I'm not left hanging

**Acceptance Criteria:**
- Bot admits uncertainty clearly
- Suggests contacting human mod
- Doesn't hallucinate wrong info

---

### Story 4: Admin Updates Documentation
**As a** project admin
**I want to** update the bot's knowledge easily
**So that** new features and changes are reflected

**Acceptance Criteria:**
- Can add new docs with a command
- Changes reflect within minutes
- No need to restart bot

---

### Story 5: Bot Works in Both Platforms
**As a** project with Telegram and Discord
**I want to** have consistent answers on both
**So that** users get the same experience everywhere

**Acceptance Criteria:**
- Same knowledge base for both
- Same response quality
- Single setup process

---

### Story 6: Admin Checks Bot Status
**As an** admin
**I want to** know if the bot is working
**So that** I can fix issues quickly

**Acceptance Criteria:**
- /status command shows health
- Alerts if bot goes offline
- View recent activity

---

### Story 7: Rate Limiting
**As a** project owner
**I want to** prevent spam/abuse
**So that** costs stay controlled

**Acceptance Criteria:**
- Max X responses per user per hour
- Ignore obvious spam
- Track usage per project

---

## 7. Technical Architecture

### System Design

```
┌─────────────────────────────────────────────────────────────┐
│                        DocBot                               │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌──────────────┐        ┌──────────────┐                  │
│  │   Telegram   │        │   Discord    │                  │
│  │   Connector  │        │   Connector  │                  │
│  └──────┬───────┘        └──────┬───────┘                  │
│         │                       │                           │
│         └───────────┬───────────┘                           │
│                     │                                       │
│                     ▼                                       │
│         ┌───────────────────────┐                          │
│         │      AI Brain         │                          │
│         │  ┌─────────────────┐  │                          │
│         │  │ Query Processor │  │                          │
│         │  └────────┬────────┘  │                          │
│         │           │           │                          │
│         │  ┌────────▼────────┐  │                          │
│         │  │  Vector Search  │  │                          │
│         │  └────────┬────────┘  │                          │
│         │           │           │                          │
│         │  ┌────────▼────────┐  │                          │
│         │  │  LLM Generator  │  │                          │
│         │  └─────────────────┘  │                          │
│         └───────────────────────┘                          │
│                     │                                       │
│                     ▼                                       │
│         ┌───────────────────────┐                          │
│         │    Knowledge Base     │                          │
│         │  ┌─────────────────┐  │                          │
│         │  │   ChromaDB      │  │                          │
│         │  │   (Vectors)     │  │                          │
│         │  └─────────────────┘  │                          │
│         └───────────────────────┘                          │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### Tech Stack

| Component | Technology | Why |
|-----------|------------|-----|
| **Language** | Python 3.11+ | Best for AI/ML, great bot libraries |
| **LLM** | Groq (free) / OpenAI (paid) | Via LiteLLM for easy switching |
| **Vector DB** | ChromaDB | Free, local, simple |
| **Embeddings** | OpenAI or HuggingFace | Convert text to vectors |
| **Telegram** | python-telegram-bot | Mature, well-documented |
| **Discord** | discord.py | Industry standard |
| **Hosting** | Railway (free tier) | Simple deploy, free credits |
| **Config** | python-dotenv | Environment variables |

### Data Flow

1. **Ingestion Flow**
   ```
   Docs (PDF/MD/URL) → Text Extraction → Chunking (500 tokens)
   → Embedding → Store in ChromaDB
   ```

2. **Query Flow**
   ```
   User Question → Embed Question → Search ChromaDB
   → Get Top 3 Chunks → LLM + Context → Response → Send to User
   ```

### File Structure

```
docbot/
├── main.py                 # Entry point
├── config.py               # Settings & API keys
├── requirements.txt        # Dependencies
│
├── brain/
│   ├── __init__.py
│   ├── ingester.py         # Load docs, chunk, embed
│   ├── vectorstore.py      # ChromaDB operations
│   └── answerer.py         # LLM response generation
│
├── connectors/
│   ├── __init__.py
│   ├── telegram_bot.py     # Telegram integration
│   └── discord_bot.py      # Discord integration
│
├── utils/
│   ├── __init__.py
│   └── helpers.py          # Shared utilities
│
├── data/
│   ├── docs/               # Uploaded documents
│   └── chroma/             # Vector database
│
└── tests/
    └── test_brain.py       # Unit tests
```

---

## 8. Success Metrics & KPIs

### North Star Metric
**Questions Answered Correctly** - The number of community questions DocBot answers that users find helpful.

### Leading Indicators

| Metric | Target (Month 1) | Target (Month 6) |
|--------|------------------|------------------|
| Bots deployed | 3 | 25 |
| Questions answered/day | 50 | 1,000 |
| Answer accuracy | 70%+ | 85%+ |
| Response time | < 5 sec | < 3 sec |
| Paying customers | 1 | 10 |
| MRR | $99 | $2,000 |

### Tracking

- Log all questions and responses
- Track "thumbs up/down" if implemented
- Monitor unanswered/escalated questions

---

## 9. Go-to-Market Strategy

### Launch Approach

**Phase 1: Friends & Family (Week 1-2)**
- Deploy for 2-3 projects you know personally
- Free in exchange for feedback
- Gather testimonials

**Phase 2: Public Launch (Week 3-4)**
- Tweet thread: "I built a bot that handles 50% of community questions"
- Demo video showing it in action
- Offer 50% discount for first 10 customers

**Phase 3: Scale (Month 2+)**
- Content: "How we handle 1,000 questions/day"
- Referral program: 1 month free for referrals
- Partner with CM communities

### Initial Channels

| Channel | Action | Expected Result |
|---------|--------|-----------------|
| Twitter/X | Build in public, launch thread | Visibility, early users |
| Discord servers | Share in CM communities | Direct leads |
| Telegram groups | Same as Discord | Direct leads |
| Direct DMs | Reach out to project founders | High conversion |

### Pricing Strategy

| Tier | Price | Features |
|------|-------|----------|
| **Starter** | $99/mo | 1 community, 1,000 questions/mo, Telegram OR Discord |
| **Growth** | $199/mo | 2 communities, 5,000 questions/mo, Telegram + Discord |
| **Pro** | $299/mo | 5 communities, unlimited questions, priority support |

**Launch offer**: 50% off first 3 months for first 10 customers.

---

## 10. Risks & Mitigations

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| Bot gives wrong answers | Medium | High | Confidence threshold, "I don't know" fallback |
| LLM costs spike | Low | Medium | Rate limiting, caching common questions |
| Competition (big players) | Medium | Medium | Stay niche (crypto), stay cheap, move fast |
| Projects don't pay | Medium | High | Start free, prove value, then convert |
| Platform TOS issues | Low | High | Follow Discord/Telegram guidelines |

---

## 11. Open Questions

1. **Should we support Slack?** - Some DAOs use it, but adds complexity
2. **Moderation features?** - Should bot detect/report bad actors?
3. **White-label option?** - How much to charge for custom branding?
4. **Analytics depth?** - Basic vs. full dashboard?
5. **Free tier?** - Offer limited free to drive adoption?

---

## 12. Timeline

| Week | Milestone |
|------|-----------|
| Week 1 | MVP complete, tested with own docs |
| Week 2 | Deploy for 2 free beta users |
| Week 3 | Polish based on feedback, launch publicly |
| Week 4 | First paying customer |
| Month 2 | 5 paying customers, $500+ MRR |
| Month 3 | 10 customers, web dashboard MVP |

---

## Appendix: Competitive Analysis

| Product | Pricing | Platforms | Target | Notes |
|---------|---------|-----------|--------|-------|
| Kapa.ai | $500+/mo | Slack, Discord | Enterprise | Too expensive for small projects |
| Mendable | $100+/mo | Web embed | Docs sites | Not for community chat |
| ChatBase | $19+/mo | Web embed | General | No Discord/Telegram |
| Keyword bots | Free | Varies | Any | Not intelligent |
| **DocBot (us)** | $99-299/mo | TG + Discord | Crypto | Crypto-native, affordable |

---

*Document version 1.0 - Ready for implementation*
