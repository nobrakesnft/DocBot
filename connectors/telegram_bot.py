"""
Telegram Bot Connector
Handles Telegram-specific message handling using the shared brain.
"""

import os
import sys
import logging

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters
)

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

    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /start command."""
        welcome_message = """
Welcome to DocBot! I'm here to answer your questions about this project.

**Commands:**
/help - Show this help message
/status - Check bot status
/ask <question> - Ask a question (or just type your question!)

Just type your question and I'll do my best to answer based on the project documentation.
        """
        await update.message.reply_text(welcome_message, parse_mode='Markdown')

    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /help command."""
        await self.start_command(update, context)

    async def status_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /status command."""
        stats = self.vector_store.get_stats()
        status_message = f"""
**DocBot Status**

Documents loaded: {stats['document_count']}
Model: {config.LLM_MODEL}
Status: Online
        """
        await update.message.reply_text(status_message, parse_mode='Markdown')

    async def ask_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /ask command."""
        # Get the question from the command
        if context.args:
            question = ' '.join(context.args)
            await self._answer_question(update, question)
        else:
            await update.message.reply_text(
                "Please include your question. Example: /ask How do I stake?"
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

        await self._answer_question(update, question)

    async def _answer_question(self, update: Update, question: str):
        """Generate and send an answer."""
        # Show typing indicator
        await update.message.chat.send_action('typing')

        try:
            # Get answer from brain
            result = self.answerer.answer(question)

            # Format response
            response = result['answer']

            # Add sources if available
            if result['sources'] and result['confidence'] > 0.5:
                sources = ', '.join(result['sources'][:3])
                response += f"\n\nSource: {sources}"

            # Send without markdown to avoid parsing errors
            await update.message.reply_text(response)

        except Exception as e:
            logger.error(f"Error answering question: {e}")
            await update.message.reply_text(
                "Sorry, I encountered an error. Please try again!"
            )

    async def reload_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Admin command to reload documents."""
        # In production, add admin check here
        docs_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "docs")

        if not os.path.exists(docs_dir):
            await update.message.reply_text(f"Docs directory not found: {docs_dir}")
            return

        try:
            # Clear existing docs
            self.vector_store.clear()

            # Load new docs
            chunks = self.ingester.load_directory(docs_dir)
            self.vector_store.add_documents(chunks)

            await update.message.reply_text(
                f"Reloaded {len(chunks)} document chunks from {docs_dir}"
            )
        except Exception as e:
            await update.message.reply_text(f"Error reloading: {e}")

    def run(self):
        """Start the Telegram bot."""
        if not config.TELEGRAM_BOT_TOKEN or config.TELEGRAM_BOT_TOKEN == "your_telegram_bot_token_here":
            print("ERROR: TELEGRAM_BOT_TOKEN not set in .env file")
            print("Get a token from @BotFather on Telegram")
            return

        # Create application
        self.app = Application.builder().token(config.TELEGRAM_BOT_TOKEN).build()

        # Add handlers
        self.app.add_handler(CommandHandler("start", self.start_command))
        self.app.add_handler(CommandHandler("help", self.help_command))
        self.app.add_handler(CommandHandler("status", self.status_command))
        self.app.add_handler(CommandHandler("ask", self.ask_command))
        self.app.add_handler(CommandHandler("reload", self.reload_command))

        # Handle regular messages
        self.app.add_handler(
            MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_message)
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
