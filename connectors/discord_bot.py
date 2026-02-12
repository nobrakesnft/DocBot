"""
Discord Bot Connector
Handles Discord-specific message handling using the shared brain.
"""

import os
import sys
import logging

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import discord
from discord.ext import commands

import config
from brain import DocumentIngester, VectorStore, Answerer

# Set up logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)


class DiscordBot:
    """Discord bot that answers questions using DocBot brain."""

    def __init__(self):
        self.ingester = DocumentIngester()
        self.vector_store = VectorStore()
        self.answerer = Answerer(self.vector_store)

        # Set up Discord intents
        intents = discord.Intents.default()
        intents.message_content = True

        # Create bot
        self.bot = commands.Bot(
            command_prefix="!",
            intents=intents,
            description="DocBot - AI Documentation Assistant"
        )

        # Register event handlers
        self._register_handlers()

    def _register_handlers(self):
        """Register all event handlers and commands."""

        @self.bot.event
        async def on_ready():
            """Called when bot is ready."""
            print(f"Discord bot logged in as {self.bot.user}")
            print(f"Connected to {len(self.bot.guilds)} server(s)")

        @self.bot.event
        async def on_message(message):
            """Handle incoming messages."""
            # Ignore bot's own messages
            if message.author == self.bot.user:
                return

            # Process commands first
            await self.bot.process_commands(message)

            # Check if bot was mentioned
            if self.bot.user in message.mentions:
                # Remove the mention from the question
                question = message.content.replace(f'<@{self.bot.user.id}>', '').strip()
                if question:
                    await self._answer_question(message, question)

        @self.bot.command(name="ask")
        async def ask_command(ctx, *, question: str = None):
            """Ask DocBot a question."""
            if not question:
                await ctx.send("Please include your question. Example: `!ask How do I stake?`")
                return
            await self._answer_question(ctx.message, question)

        @self.bot.command(name="docbot")
        async def docbot_command(ctx, *, question: str = None):
            """Alias for !ask."""
            if not question:
                await ctx.send("Please include your question. Example: `!docbot How do I stake?`")
                return
            await self._answer_question(ctx.message, question)

        @self.bot.command(name="status")
        async def status_command(ctx):
            """Check DocBot status."""
            stats = self.vector_store.get_stats()

            embed = discord.Embed(
                title="DocBot Status",
                color=discord.Color.green()
            )
            embed.add_field(name="Documents Loaded", value=stats['document_count'], inline=True)
            embed.add_field(name="Model", value=config.LLM_MODEL.split('/')[-1], inline=True)
            embed.add_field(name="Status", value="Online", inline=True)

            await ctx.send(embed=embed)

        @self.bot.command(name="help_docbot")
        async def help_docbot_command(ctx):
            """Show DocBot help."""
            embed = discord.Embed(
                title="DocBot Help",
                description="I answer questions based on project documentation!",
                color=discord.Color.blue()
            )
            embed.add_field(
                name="Commands",
                value="""
`!ask <question>` - Ask a question
`!docbot <question>` - Same as !ask
`!status` - Check bot status
`@DocBot <question>` - Mention me with a question
                """,
                inline=False
            )
            embed.add_field(
                name="Examples",
                value="""
`!ask How do I stake?`
`!docbot What wallets are supported?`
`@DocBot What is the APY?`
                """,
                inline=False
            )

            await ctx.send(embed=embed)

        @self.bot.command(name="reload")
        @commands.has_permissions(administrator=True)
        async def reload_command(ctx):
            """Admin command to reload documents."""
            docs_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "docs")

            if not os.path.exists(docs_dir):
                await ctx.send(f"Docs directory not found: `{docs_dir}`")
                return

            try:
                # Clear existing docs
                self.vector_store.clear()

                # Load new docs
                chunks = self.ingester.load_directory(docs_dir)
                self.vector_store.add_documents(chunks)

                await ctx.send(f"Reloaded {len(chunks)} document chunks!")
            except Exception as e:
                await ctx.send(f"Error reloading: {e}")

    async def _answer_question(self, message, question: str):
        """Generate and send an answer."""
        # Show typing indicator
        async with message.channel.typing():
            try:
                # Get answer from brain
                result = self.answerer.answer(question)

                # Create embed for nice formatting
                embed = discord.Embed(
                    description=result['answer'],
                    color=discord.Color.blue()
                )

                # Add sources if available
                if result['sources'] and result['confidence'] > 0.5:
                    sources = ', '.join(result['sources'][:3])
                    embed.set_footer(text=f"Source: {sources}")

                await message.channel.send(embed=embed)

            except Exception as e:
                logger.error(f"Error answering question: {e}")
                await message.channel.send(
                    "Sorry, I encountered an error. Please try again!"
                )

    def run(self):
        """Start the Discord bot."""
        if not config.DISCORD_BOT_TOKEN or config.DISCORD_BOT_TOKEN == "your_discord_bot_token_here":
            print("ERROR: DISCORD_BOT_TOKEN not set in .env file")
            print("Get a token from the Discord Developer Portal:")
            print("https://discord.com/developers/applications")
            return

        print("Starting Discord bot...")
        print("Press Ctrl+C to stop")
        self.bot.run(config.DISCORD_BOT_TOKEN)


# =============================================================================
# Run directly
# =============================================================================

if __name__ == "__main__":
    bot = DiscordBot()
    bot.run()
