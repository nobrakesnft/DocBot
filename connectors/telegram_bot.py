"""
Telegram Bot Connector
Handles Telegram-specific message handling using the shared brain.
Self-explanatory UX - anyone can use it without coding knowledge.
"""

import os
import sys
import logging
import random
import asyncio

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from telegram import Update, BotCommand
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
    Defaults
)
from telegram.request import HTTPXRequest

import config
from brain import DocumentIngester, VectorStore, Answerer
from connectors import bot_utils

# Set up logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)


class TelegramBot:
    """Telegram bot that answers questions using DocBot brain."""

    def __init__(self):
        self.ingester = DocumentIngester()
        self.vector_store = VectorStore()
        self.answerer = Answerer(self.vector_store)
        self.app = None

    def _get_project_id(self, chat) -> str:
        """Get project ID from chat. Groups have isolated docs, DMs use default."""
        if chat.type in ["group", "supergroup"]:
            return f"telegram_{chat.id}"
        return "default"

    def _get_doc_count(self, project_id: str) -> int:
        """Get document count for a project."""
        return self.vector_store.count(project_id)

    def _get_suggested_questions(self, project_id: str) -> str:
        """Generate suggested questions based on loaded docs."""
        doc_count = self._get_doc_count(project_id)
        if doc_count == 0:
            return ""

        return """
💡 Try asking:
• "How do I get started?"
• "What are the tokenomics?"
• "How does staking work?"
• Or ask anything about the project!"""

    # =========================================================================
    # WELCOME & HELP
    # =========================================================================

    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /start command - friendly onboarding."""
        project_id = self._get_project_id(update.message.chat)
        doc_count = self._get_doc_count(project_id)
        chat_type = update.message.chat.type

        if chat_type in ["group", "supergroup"]:
            # Group welcome
            welcome = f"""👋 Hey! I'm DocBot - your AI documentation assistant!

I answer questions based on your project's docs, so your community gets instant help 24/7.

📊 Current Status: {doc_count} document chunks loaded

"""
            if doc_count == 0:
                welcome += """🚀 QUICK SETUP (Admins):
1️⃣ /loaddoc then upload a file (.txt, .md, .pdf)
2️⃣ Or use: /load_url https://your-docs-site.com

Once docs are loaded, anyone can ask questions!
"""
            else:
                welcome += """✅ I'm ready to answer questions!

Just type your question or use /ask <question>
"""
                welcome += self._get_suggested_questions(project_id)

        else:
            # DM welcome
            welcome = f"""👋 Hey! I'm DocBot - your AI documentation assistant!

I answer questions based on project documentation.

📊 Status: {doc_count} document chunks loaded

"""
            if doc_count == 0:
                welcome += """📄 To get started:
• /loaddoc then upload a file (.txt, .md, .pdf)
• Or use: /load_url https://docs-site.com
• Or use: /load_text <paste your text here>

Then just ask me questions!
"""
            else:
                welcome += """Just send me your question and I'll find the answer!
"""
                welcome += self._get_suggested_questions(project_id)

        welcome += """
Type /help for all commands."""

        await update.message.reply_text(welcome)

    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /help command - clear, categorized help."""
        project_id = self._get_project_id(update.message.chat)
        doc_count = self._get_doc_count(project_id)

        help_text = """📚 DOCBOT HELP

━━━ FOR EVERYONE ━━━
• Just type your question - I'll answer it!
• /ask <question> - Ask a specific question
• /status - Check if docs are loaded

━━━ FOR ADMINS ━━━
📄 Adding Documentation:
• /loaddoc - Then upload a file (.txt, .md, .pdf)
• /load_url <link> - Load from a website
• /load_text <text> - Add text directly

🔧 Management:
• /docs_info - See what's loaded
• /clear_docs - Remove all docs (start fresh)

━━━ EXAMPLES ━━━
Ask: "How do I stake my tokens?"
Ask: "What wallets are supported?"
Ask: "What is the max supply?"

"""
        help_text += f"📊 Currently loaded: {doc_count} document chunks"

        if doc_count == 0:
            help_text += "\n\n⚠️ No docs loaded yet! Admins: upload a file or use /load_url to get started."

        await update.message.reply_text(help_text)

    async def status_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /status command - friendly status check."""
        project_id = self._get_project_id(update.message.chat)
        doc_count = self._get_doc_count(project_id)

        if doc_count > 0:
            status = f"""✅ DocBot is ready!

📊 Documents loaded: {doc_count} chunks
🤖 AI Model: {config.LLM_MODEL.split('/')[-1]}
💬 Status: Online and ready to answer

Just type your question!"""
        else:
            status = """⚠️ No documents loaded yet!

To get started, an admin needs to:
1️⃣ Drop a file here (.txt, .md, .pdf)
2️⃣ Or use /load_url https://your-docs.com

Once docs are loaded, I can answer questions!"""

        await update.message.reply_text(status)

    async def setup_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /setup command - guided onboarding for admins."""
        project_id = self._get_project_id(update.message.chat)
        doc_count = self._get_doc_count(project_id)

        if doc_count > 0:
            # Already set up
            setup_text = f"""✅ DocBot is already set up!

📊 Status: {doc_count} doc chunks loaded
🤖 Ready to answer questions

━━━ QUICK ACTIONS ━━━
• /docs_info - See what's loaded
• /load_url <link> - Add more docs
• /clear_docs - Start fresh

━━━ TEST IT ━━━
Try asking: "How do I get started?"

Need to add a new project's docs? Use /clear_docs first, then upload new files."""
        else:
            # Fresh setup
            setup_text = """👋 Let's set up DocBot for your project!

━━━ STEP 1: ADD YOUR DOCS ━━━
Choose one:
📄 /loaddoc then upload a file (.txt, .md, .pdf)
🔗 Use: /load_url https://your-docs-site.com
📝 Use: /load_text <paste your FAQ here>

━━━ STEP 2: TEST IT ━━━
Once loaded, ask a question like:
"How do I stake?" or "What's the tokenomics?"

━━━ STEP 3: DONE! ━━━
Your community can now ask questions 24/7

━━━ PRO TIPS ━━━
• Upload your whitepaper, FAQ, or gitbook
• More docs = better answers
• Bot auto-learns from what you upload

Questions? Just ask!"""

        await update.message.reply_text(setup_text)

    # =========================================================================
    # ASKING QUESTIONS
    # =========================================================================

    async def ask_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /ask command."""
        if context.args:
            question = ' '.join(context.args)

            # Check if this is a reply to another message - include that context
            if update.message.reply_to_message and update.message.reply_to_message.text:
                replied_content = update.message.reply_to_message.text[:500]
                question = f'[Regarding: "{replied_content}"]\n\n{question}'

            # Rate limiting
            user_id = str(update.message.from_user.id)
            is_allowed, remaining = bot_utils.check_cooldown(user_id)
            if not is_allowed:
                await update.message.reply_text(f"chill, gimme like {remaining}s 😅")
                return

            project_id = self._get_project_id(update.message.chat)
            await self._answer_question(update, question, project_id)
            bot_utils.record_question(user_id)
        else:
            # No question provided - check if replying to a message
            if update.message.reply_to_message and update.message.reply_to_message.text:
                replied_content = update.message.reply_to_message.text[:500]
                question = f'[Regarding: "{replied_content}"]\n\nExplain this or answer any question in it'

                user_id = str(update.message.from_user.id)
                is_allowed, remaining = bot_utils.check_cooldown(user_id)
                if not is_allowed:
                    await update.message.reply_text(f"chill, gimme like {remaining}s 😅")
                    return

                project_id = self._get_project_id(update.message.chat)
                await self._answer_question(update, question, project_id)
                bot_utils.record_question(user_id)
            else:
                await update.message.reply_text(
                    "just ask! like: /ask how do I stake?"
                )

    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle regular messages - smart detection for when to respond."""
        question = update.message.text
        chat_type = update.message.chat.type

        # Ignore very short messages
        if len(question) < 3:
            return

        # Ignore messages that look like commands
        if question.startswith('/'):
            return

        # Check if this is a reply to another message - include that context
        if update.message.reply_to_message and update.message.reply_to_message.text:
            replied_content = update.message.reply_to_message.text[:500]  # Limit length
            question = f'[Regarding: "{replied_content}"]\n\n{question}'

        # Check if it should be ignored (greetings, reactions, etc.)
        # Only check the original question part, not the prepended context
        original_question = update.message.text
        if bot_utils.should_ignore(original_question):
            # In DMs, maybe respond to greetings casually
            if chat_type == "private" and bot_utils.is_greeting(original_question):
                greetings = ["gm!", "hey 👋", "yo, got a question?", "gm gm"]
                await update.message.reply_text(random.choice(greetings))
            return

        # In groups: only respond if it looks like a question OR it's a reply to a message
        # Replies to messages should always be answered (user is asking about that message)
        if chat_type in ["group", "supergroup"]:
            is_reply = update.message.reply_to_message is not None
            if not is_reply and not bot_utils.is_question(original_question):
                # Not a question and not a reply in group chat - stay quiet
                return

        # Rate limiting
        user_id = str(update.message.from_user.id)
        is_allowed, remaining = bot_utils.check_cooldown(user_id)
        if not is_allowed:
            await update.message.reply_text(f"chill, gimme like {remaining}s 😅")
            return

        project_id = self._get_project_id(update.message.chat)
        await self._answer_question(update, question, project_id)
        bot_utils.record_question(user_id)

    async def _answer_question(self, update: Update, question: str, project_id: str = "default"):
        """Generate and send an answer for a specific project."""
        chat_id = str(update.message.chat.id)
        doc_count = self._get_doc_count(project_id)

        # Step 1: Check if docs are loaded
        if doc_count == 0:
            await update.message.reply_text(
                "no docs loaded yet - an admin needs to add some first"
            )
            return

        # Step 2: Check for cached duplicate answer
        cached = bot_utils.find_cached_answer(question, project_id)
        if cached:
            # Extract topic for contextual response
            topic = bot_utils.extract_topic(question)

            # Track repeat count per chat+topic
            cache_key = f"{chat_id}:{topic}"
            repeat_count = bot_utils.get_repeat_count(cache_key)

            # Get sassy response with topic
            response = bot_utils.get_smart_duplicate_response(topic, repeat_count)

            if response:
                # Reply to original cached message if possible
                try:
                    await update.message.reply_text(
                        response,
                        reply_to_message_id=int(cached['message_ref']) if cached['message_ref'].isdigit() else None
                    )
                except:
                    await update.message.reply_text(response)
            # If None, stay silent
            return

        # Show typing indicator
        await update.message.chat.send_action('typing')

        # Human-like delay
        await bot_utils.human_typing_delay()

        try:
            # Get answer from brain
            result = self.answerer.answer(question, project_id=project_id)

            # Reply to the question (quotes it)
            reply_msg = await update.message.reply_text(result['answer'])

            # Cache the answer with message ID
            bot_utils.cache_answer(
                question=question,
                answer=result['answer'],
                project_id=project_id,
                message_ref=str(reply_msg.message_id),
                user_id=str(update.message.from_user.id)
            )

        except Exception as e:
            logger.error(f"Error answering question: {e}")
            error_responses = [
                "ah something went wrong, try again?",
                "oops hit an error there, mind rephrasing?",
                "hmm broke something, try again maybe?",
            ]
            await update.message.reply_text(random.choice(error_responses))

    # =========================================================================
    # DOCUMENT MANAGEMENT
    # =========================================================================

    async def docs_info_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show document info for this chat."""
        project_id = self._get_project_id(update.message.chat)
        doc_count = self._get_doc_count(project_id)

        if doc_count == 0:
            await update.message.reply_text(
                "📭 No documents loaded yet!\n\n"
                "To add docs:\n"
                "• /loaddoc then upload a file (.txt, .md, .pdf)\n"
                "• Or use /load_url https://your-docs.com"
            )
            return

        # Get sources
        project_docs = [d for d in self.vector_store.documents if d.get("project_id") == project_id]
        sources = list(set(d.get("source", "unknown") for d in project_docs))

        message = f"""📚 Documentation Info

📊 Total chunks: {doc_count}
📄 Sources: {len(sources)}

"""
        for source in sources[:5]:
            message += f"• {source}\n"

        if len(sources) > 5:
            message += f"• ... and {len(sources) - 5} more"

        message += "\n✅ Ready to answer questions!"

        await update.message.reply_text(message)

    async def _is_admin(self, update: Update) -> bool:
        """Check if user is admin in groups. Returns True for DMs."""
        chat_type = update.message.chat.type
        if chat_type in ["group", "supergroup"]:
            user_id = update.message.from_user.id
            member = await update.message.chat.get_member(user_id)
            return member.status in ["administrator", "creator"]
        return True  # DMs - user controls their own bot

    async def clear_docs_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Clear all documents for this chat. Admin only in groups."""
        if not await self._is_admin(update):
            await update.message.reply_text("⚠️ Only admins can clear documents.")
            return

        project_id = self._get_project_id(update.message.chat)
        doc_count = self._get_doc_count(project_id)

        if doc_count == 0:
            await update.message.reply_text("📭 No documents to clear!")
            return

        removed = self.vector_store.clear_project(project_id)
        await update.message.reply_text(
            f"🗑️ Cleared {removed} document chunks!\n\n"
            "To add new docs:\n"
            "• /loaddoc then upload a file (.txt, .md, .pdf)\n"
            "• Or use /load_url https://your-docs.com"
        )

    async def load_text_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Load documentation from text directly. Admin only in groups."""
        if not await self._is_admin(update):
            await update.message.reply_text("⚠️ Only admins can add documents.")
            return

        if not context.args:
            await update.message.reply_text(
                "📝 Please provide the text to add!\n\n"
                "Example:\n"
                "/load_text Our project offers 10% APY staking. "
                "Supported wallets include MetaMask and WalletConnect."
            )
            return

        text = ' '.join(context.args)
        project_id = self._get_project_id(update.message.chat)

        try:
            chunks = self.ingester.load_text(text, source="manual_input")
            self.vector_store.add_documents(chunks, project_id=project_id)

            total_docs = self._get_doc_count(project_id)

            await update.message.reply_text(
                f"✅ Added {len(chunks)} chunk(s) to knowledge base!\n\n"
                f"📊 Total documents: {total_docs} chunks\n\n"
                f"I'm ready to answer questions about this content!"
                f"{self._get_suggested_questions(project_id)}"
            )
        except Exception as e:
            await update.message.reply_text(f"❌ Error adding text: {e}")

    async def load_url_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Load documentation from a URL. Admin only in groups."""
        if not await self._is_admin(update):
            await update.message.reply_text("⚠️ Only admins can add documents.")
            return

        if not context.args:
            await update.message.reply_text(
                "🔗 Please provide a URL!\n\n"
                "Example:\n"
                "/load_url https://docs.yourproject.com/faq"
            )
            return

        url = context.args[0]
        project_id = self._get_project_id(update.message.chat)

        await update.message.reply_text(f"🔄 Loading docs from URL...\n{url}")

        try:
            chunks = self.ingester.load_url(url)
            if chunks:
                self.vector_store.add_documents(chunks, project_id=project_id)
                total_docs = self._get_doc_count(project_id)

                await update.message.reply_text(
                    f"✅ Loaded {len(chunks)} chunks from URL!\n\n"
                    f"📊 Total documents: {total_docs} chunks\n\n"
                    f"I'm ready to answer questions!"
                    f"{self._get_suggested_questions(project_id)}"
                )
            else:
                await update.message.reply_text(
                    "⚠️ Couldn't extract content from that URL.\n\n"
                    "Try a different page, or use /load_text to paste content directly."
                )
        except Exception as e:
            await update.message.reply_text(
                f"❌ Error loading URL: {e}\n\n"
                "Make sure the URL is correct and accessible."
            )

    async def loaddoc_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /loaddoc command - waits for user to upload a document. Admin only in groups."""
        if not await self._is_admin(update):
            await update.message.reply_text("⚠️ Only admins can load documents.")
            return

        # Set waiting state for this user in this chat
        chat_id = update.message.chat.id
        user_id = update.message.from_user.id

        if 'waiting_for_doc' not in context.bot_data:
            context.bot_data['waiting_for_doc'] = {}

        context.bot_data['waiting_for_doc'][f"{chat_id}:{user_id}"] = True

        await update.message.reply_text(
            "📄 Please upload a document now (.txt, .md, .pdf)\n\n"
            "I'm waiting for your file..."
        )

    async def handle_document(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle document uploads - only processes if user used /loaddoc first."""
        chat_id = update.message.chat.id
        user_id = update.message.from_user.id
        waiting_key = f"{chat_id}:{user_id}"

        # Check if this user is waiting to upload a doc
        waiting_for_doc = context.bot_data.get('waiting_for_doc', {})
        if not waiting_for_doc.get(waiting_key):
            # Not waiting - ignore the document
            return

        # Clear the waiting state
        context.bot_data['waiting_for_doc'][waiting_key] = False

        # Admin check (in case someone else uploads while admin is waiting)
        if not await self._is_admin(update):
            return

        document = update.message.document
        file_name = document.file_name.lower()

        # Check supported formats
        supported = ['.txt', '.md', '.pdf']
        if not any(file_name.endswith(ext) for ext in supported):
            await update.message.reply_text(
                f"⚠️ Unsupported file format!\n\n"
                f"Supported formats: {', '.join(supported)}\n\n"
                f"You uploaded: {document.file_name}"
            )
            return

        project_id = self._get_project_id(update.message.chat)
        await update.message.reply_text(f"📄 Processing {document.file_name}...")

        try:
            # Download file
            file = await context.bot.get_file(document.file_id)
            file_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "temp", document.file_name)
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            await file.download_to_drive(file_path)

            # Load and process
            chunks = self.ingester.load_file(file_path)
            if chunks:
                self.vector_store.add_documents(chunks, project_id=project_id)
                total_docs = self._get_doc_count(project_id)

                await update.message.reply_text(
                    f"✅ Loaded {len(chunks)} chunks from {document.file_name}!\n\n"
                    f"📊 Total documents: {total_docs} chunks\n\n"
                    f"I'm ready to answer questions about this content!"
                    f"{self._get_suggested_questions(project_id)}"
                )
            else:
                await update.message.reply_text(
                    f"⚠️ Couldn't extract content from {document.file_name}.\n\n"
                    "The file might be empty or in an unsupported format."
                )

            # Cleanup
            os.remove(file_path)

        except Exception as e:
            logger.error(f"Error processing file: {e}")
            await update.message.reply_text(
                f"❌ Error processing file: {e}\n\n"
                "Please try again or use a different file."
            )

    async def reload_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Admin command to reload documents for THIS chat."""
        if not await self._is_admin(update):
            await update.message.reply_text("⚠️ Only admins can reload documents.")
            return

        project_id = self._get_project_id(update.message.chat)
        docs_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "docs", project_id)

        if not os.path.exists(docs_dir):
            await update.message.reply_text(
                f"📭 No local docs folder found for this chat.\n\n"
                f"Use /load_url or drop a file to add docs!"
            )
            return

        try:
            await update.message.reply_text("🔄 Reloading documents...")

            # Clear existing docs for THIS chat only
            self.vector_store.clear_project(project_id)

            # Load new docs
            chunks = self.ingester.load_directory(docs_dir)
            self.vector_store.add_documents(chunks, project_id=project_id)

            await update.message.reply_text(
                f"✅ Reloaded {len(chunks)} document chunks!\n\n"
                f"I'm ready to answer questions!"
            )
        except Exception as e:
            await update.message.reply_text(f"❌ Error reloading: {e}")

    async def set_tone_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Set the response tone for this chat. Admin only in groups."""
        if not await self._is_admin(update):
            await update.message.reply_text("⚠️ Only admins can change the tone.")
            return

        if not context.args:
            # Show current tone and options
            project_id = self._get_project_id(update.message.chat)
            current_tone = bot_utils.get_project_tone(project_id)

            await update.message.reply_text(
                f"🎨 RESPONSE TONE SETTINGS\n\n"
                f"Current tone: **{current_tone}**\n\n"
                f"━━━ AVAILABLE TONES ━━━\n\n"
                f"📱 casual\n"
                f"Friendly, web3-native, light slang\n"
                f'Example: "No exact date yet, snapshot is planned for Q2 2026 👀"\n\n'
                f"📝 neutral\n"
                f"Friendly but clean, no slang\n"
                f'Example: "Snapshot is planned for Q2 2026, but no exact date has been announced yet."\n\n'
                f"💼 professional\n"
                f"Formal support tone\n"
                f'Example: "The snapshot is scheduled for Q2 2026. An exact date has not yet been announced."\n\n'
                f"━━━ USAGE ━━━\n"
                f"/set_tone casual\n"
                f"/set_tone neutral\n"
                f"/set_tone professional",
                parse_mode="Markdown"
            )
            return

        tone = context.args[0].lower()
        project_id = self._get_project_id(update.message.chat)

        if bot_utils.set_project_tone(project_id, tone):
            tone_descriptions = {
                "casual": "Friendly, web3-native, light slang allowed 🤙",
                "neutral": "Friendly but clean, no slang or emojis",
                "professional": "Formal support tone, precise language",
            }
            examples = {
                "casual": '"No exact date yet, snapshot is planned for Q2 2026 👀"',
                "neutral": '"Snapshot is planned for Q2 2026, but no exact date has been announced yet."',
                "professional": '"The snapshot is scheduled for Q2 2026. An exact date has not yet been announced."',
            }

            await update.message.reply_text(
                f"🎨 Tone Updated!\n\n"
                f"New tone: **{tone}**\n"
                f"Style: {tone_descriptions[tone]}\n\n"
                f"Example response:\n{examples[tone]}",
                parse_mode="Markdown"
            )
        else:
            await update.message.reply_text(
                "❌ Invalid tone!\n\n"
                "Choose: casual, neutral, or professional\n\n"
                "Example: /set_tone professional"
            )

    # =========================================================================
    # BOT SETUP
    # =========================================================================

    async def post_init(self, application):
        """Set up bot commands menu."""
        commands = [
            BotCommand("start", "👋 Get started with DocBot"),
            BotCommand("setup", "🚀 Quick setup guide"),
            BotCommand("help", "📚 Show all commands"),
            BotCommand("ask", "❓ Ask a question"),
            BotCommand("status", "📊 Check bot status"),
            BotCommand("docs_info", "📄 See loaded docs"),
            BotCommand("loaddoc", "📄 Upload a document"),
            BotCommand("load_url", "🔗 Load docs from URL"),
            BotCommand("set_tone", "🎨 Set response tone"),
            BotCommand("clear_docs", "🗑️ Clear all docs"),
        ]
        await application.bot.set_my_commands(commands)

    def run(self):
        """Start the Telegram bot."""
        if not config.TELEGRAM_BOT_TOKEN or config.TELEGRAM_BOT_TOKEN == "your_telegram_bot_token_here":
            print("ERROR: TELEGRAM_BOT_TOKEN not set in .env file")
            print("Get a token from @BotFather on Telegram")
            return

        # Create custom request with longer timeouts
        request = HTTPXRequest(
            connection_pool_size=8,
            connect_timeout=30.0,
            read_timeout=30.0,
            write_timeout=30.0,
            pool_timeout=30.0
        )

        # Create application with custom request
        self.app = (
            Application.builder()
            .token(config.TELEGRAM_BOT_TOKEN)
            .request(request)
            .post_init(self.post_init)
            .build()
        )

        # Add handlers
        self.app.add_handler(CommandHandler("start", self.start_command))
        self.app.add_handler(CommandHandler("setup", self.setup_command))
        self.app.add_handler(CommandHandler("help", self.help_command))
        self.app.add_handler(CommandHandler("status", self.status_command))
        self.app.add_handler(CommandHandler("ask", self.ask_command))
        self.app.add_handler(CommandHandler("reload", self.reload_command))
        self.app.add_handler(CommandHandler("docs_info", self.docs_info_command))
        self.app.add_handler(CommandHandler("clear_docs", self.clear_docs_command))
        self.app.add_handler(CommandHandler("load_text", self.load_text_command))
        self.app.add_handler(CommandHandler("load_url", self.load_url_command))
        self.app.add_handler(CommandHandler("loaddoc", self.loaddoc_command))
        self.app.add_handler(CommandHandler("set_tone", self.set_tone_command))

        # Handle regular messages
        self.app.add_handler(
            MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_message)
        )

        # Handle document uploads (only processes after /loaddoc)
        self.app.add_handler(
            MessageHandler(filters.Document.ALL, self.handle_document)
        )

        # Start the bot
        print("Starting Telegram bot...")
        print("Press Ctrl+C to stop")
        self.app.run_polling(allowed_updates=Update.ALL_TYPES)


# =============================================================================
# Run directly
# =============================================================================

if __name__ == "__main__":
    bot = TelegramBot()
    bot.run()
