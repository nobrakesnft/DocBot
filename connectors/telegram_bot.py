"""
Telegram Bot Connector
Handles Telegram-specific message handling using the shared brain.
Self-explanatory UX - anyone can use it without coding knowledge.
"""

import os
import sys
import logging

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
1️⃣ Drop a file here (.txt, .md, or .pdf)
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
• Send me a document file (.txt, .md, .pdf)
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
• Drop a file (.txt, .md, .pdf) in chat
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

    # =========================================================================
    # ASKING QUESTIONS
    # =========================================================================

    async def ask_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /ask command."""
        if context.args:
            question = ' '.join(context.args)
            project_id = self._get_project_id(update.message.chat)
            await self._answer_question(update, question, project_id)
        else:
            await update.message.reply_text(
                "❓ Please include your question!\n\n"
                "Example: /ask How do I stake my tokens?"
            )

    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle regular messages as questions."""
        question = update.message.text

        # Ignore very short messages
        if len(question) < 3:
            return

        # Ignore messages that look like commands
        if question.startswith('/'):
            return

        project_id = self._get_project_id(update.message.chat)
        await self._answer_question(update, question, project_id)

    async def _answer_question(self, update: Update, question: str, project_id: str = "default"):
        """Generate and send an answer for a specific project."""
        doc_count = self._get_doc_count(project_id)

        # Check if docs are loaded
        if doc_count == 0:
            await update.message.reply_text(
                "📭 I don't have any documentation loaded yet!\n\n"
                "An admin needs to:\n"
                "• Drop a file here (.txt, .md, .pdf)\n"
                "• Or use /load_url https://your-docs.com\n\n"
                "Once docs are loaded, I can answer questions!"
            )
            return

        # Show typing indicator
        await update.message.chat.send_action('typing')

        try:
            # Get answer from brain
            result = self.answerer.answer(question, project_id=project_id)
            response = result['answer']

            # Add source info if confident
            if result['sources'] and result['confidence'] > 0.5:
                sources = ', '.join(result['sources'][:2])
                response += f"\n\n📄 Source: {sources}"

            await update.message.reply_text(response)

        except Exception as e:
            logger.error(f"Error answering question: {e}")
            await update.message.reply_text(
                "😅 Sorry, I had trouble answering that. Please try again!\n\n"
                "If this keeps happening, try rephrasing your question."
            )

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
                "• Drop a file here (.txt, .md, .pdf)\n"
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

    async def clear_docs_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Clear all documents for this chat."""
        project_id = self._get_project_id(update.message.chat)
        doc_count = self._get_doc_count(project_id)

        if doc_count == 0:
            await update.message.reply_text("📭 No documents to clear!")
            return

        removed = self.vector_store.clear_project(project_id)
        await update.message.reply_text(
            f"🗑️ Cleared {removed} document chunks!\n\n"
            "To add new docs:\n"
            "• Drop a file here (.txt, .md, .pdf)\n"
            "• Or use /load_url https://your-docs.com"
        )

    async def load_text_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Load documentation from text directly."""
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
        """Load documentation from a URL."""
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

    async def handle_document(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle file uploads."""
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

    # =========================================================================
    # BOT SETUP
    # =========================================================================

    async def post_init(self, application):
        """Set up bot commands menu."""
        commands = [
            BotCommand("start", "👋 Get started with DocBot"),
            BotCommand("help", "📚 Show all commands"),
            BotCommand("ask", "❓ Ask a question"),
            BotCommand("status", "📊 Check bot status"),
            BotCommand("docs_info", "📄 See loaded docs"),
            BotCommand("load_url", "🔗 Load docs from URL"),
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
        self.app.add_handler(CommandHandler("help", self.help_command))
        self.app.add_handler(CommandHandler("status", self.status_command))
        self.app.add_handler(CommandHandler("ask", self.ask_command))
        self.app.add_handler(CommandHandler("reload", self.reload_command))
        self.app.add_handler(CommandHandler("docs_info", self.docs_info_command))
        self.app.add_handler(CommandHandler("clear_docs", self.clear_docs_command))
        self.app.add_handler(CommandHandler("load_text", self.load_text_command))
        self.app.add_handler(CommandHandler("load_url", self.load_url_command))

        # Handle regular messages
        self.app.add_handler(
            MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_message)
        )

        # Handle file uploads
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
