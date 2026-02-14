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

    def _get_project_id(self, chat) -> str:
        """Get project ID from chat. Groups have isolated docs, DMs use default."""
        if chat.type in ["group", "supergroup"]:
            return f"telegram_{chat.id}"
        return "default"

    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /start command."""
        welcome_message = """Welcome to DocBot! I answer questions based on project docs.

User Commands:
/ask <question> - Ask a question
/status - Check bot status

Admin Commands:
/docs_info - Show loaded docs info
/load_text <text> - Add text to knowledge base
/load_url <url> - Load docs from URL
/clear_docs - Clear docs for this chat
/reload - Reload docs from folder

Or just upload a file (.txt, .md, .pdf)!
        """
        await update.message.reply_text(welcome_message)

    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /help command."""
        await self.start_command(update, context)

    async def status_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /status command."""
        project_id = self._get_project_id(update.message.chat)
        doc_count = self.vector_store.count(project_id)

        status_message = f"""DocBot Status

Documents loaded: {doc_count}
Model: {config.LLM_MODEL}
Status: Online
Chat ID: {project_id}
        """
        await update.message.reply_text(status_message)

    async def ask_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /ask command."""
        # Get the question from the command
        if context.args:
            question = ' '.join(context.args)
            project_id = self._get_project_id(update.message.chat)
            await self._answer_question(update, question, project_id)
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

        project_id = self._get_project_id(update.message.chat)
        await self._answer_question(update, question, project_id)

    async def _answer_question(self, update: Update, question: str, project_id: str = "default"):
        """Generate and send an answer for a specific project."""
        # Show typing indicator
        await update.message.chat.send_action('typing')

        try:
            # Get answer from brain (project-specific)
            result = self.answerer.answer(question, project_id=project_id)

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
        """Admin command to reload documents for THIS chat."""
        project_id = self._get_project_id(update.message.chat)
        docs_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "docs", project_id)

        if not os.path.exists(docs_dir):
            await update.message.reply_text(f"No docs folder for this chat. Create: data/docs/{project_id}/")
            return

        try:
            # Clear existing docs for THIS chat only
            self.vector_store.clear_project(project_id)

            # Load new docs
            chunks = self.ingester.load_directory(docs_dir)
            self.vector_store.add_documents(chunks, project_id=project_id)

            await update.message.reply_text(f"Reloaded {len(chunks)} document chunks!")
        except Exception as e:
            await update.message.reply_text(f"Error reloading: {e}")

    async def docs_info_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show document info for this chat."""
        project_id = self._get_project_id(update.message.chat)
        doc_count = self.vector_store.count(project_id)

        # Get sources
        project_docs = [d for d in self.vector_store.documents if d.get("project_id") == project_id]
        sources = list(set(d.get("source", "unknown") for d in project_docs))

        message = f"""Documentation Info

Chat ID: {project_id}
Documents: {doc_count}
Sources: {', '.join(sources[:5]) if sources else 'None'}
        """
        await update.message.reply_text(message)

    async def clear_docs_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Clear all documents for this chat."""
        project_id = self._get_project_id(update.message.chat)
        removed = self.vector_store.clear_project(project_id)
        await update.message.reply_text(f"Cleared {removed} documents for this chat.")

    async def load_text_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Load documentation from text directly."""
        if not context.args:
            await update.message.reply_text("Please provide text. Example: /load_text Our project offers 10% APY...")
            return

        text = ' '.join(context.args)
        project_id = self._get_project_id(update.message.chat)

        try:
            chunks = self.ingester.load_text(text, source="telegram_input")
            self.vector_store.add_documents(chunks, project_id=project_id)
            await update.message.reply_text(f"Added {len(chunks)} chunks to knowledge base!")
        except Exception as e:
            await update.message.reply_text(f"Error: {e}")

    async def load_url_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Load documentation from a URL."""
        if not context.args:
            await update.message.reply_text("Please provide a URL. Example: /load_url https://docs.example.com/faq")
            return

        url = context.args[0]
        project_id = self._get_project_id(update.message.chat)

        await update.message.reply_text(f"Loading docs from URL...")

        try:
            chunks = self.ingester.load_url(url)
            if chunks:
                self.vector_store.add_documents(chunks, project_id=project_id)
                await update.message.reply_text(f"Loaded {len(chunks)} chunks from {url}")
            else:
                await update.message.reply_text("Could not extract any content from that URL.")
        except Exception as e:
            await update.message.reply_text(f"Error loading URL: {e}")

    async def handle_document(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle file uploads."""
        document = update.message.document
        file_name = document.file_name.lower()

        # Check supported formats
        if not any(file_name.endswith(ext) for ext in ['.txt', '.md', '.pdf']):
            await update.message.reply_text("Supported formats: .txt, .md, .pdf")
            return

        project_id = self._get_project_id(update.message.chat)
        await update.message.reply_text(f"Processing {document.file_name}...")

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
                await update.message.reply_text(f"Loaded {len(chunks)} chunks from {document.file_name}")
            else:
                await update.message.reply_text("Could not extract any content from that file.")

            # Cleanup
            os.remove(file_path)

        except Exception as e:
            logger.error(f"Error processing file: {e}")
            await update.message.reply_text(f"Error processing file: {e}")

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
