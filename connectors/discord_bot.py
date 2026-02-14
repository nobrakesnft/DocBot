"""
Discord Bot Connector
Handles Discord-specific message handling using the shared brain.
Uses slash commands (/) for all interactions.
"""

import os
import sys
import logging
import aiohttp

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import discord
from discord import app_commands
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

        # Create bot with slash commands
        self.bot = commands.Bot(
            command_prefix="/",
            intents=intents,
            description="DocBot - AI Documentation Assistant"
        )

        # Register event handlers
        self._register_handlers()

    def _get_project_id(self, guild) -> str:
        """Get project ID from guild/server. Each server has isolated docs."""
        if guild:
            return f"discord_{guild.id}"
        return "default"

    def _register_handlers(self):
        """Register all event handlers and slash commands."""

        @self.bot.event
        async def on_ready():
            """Called when bot is ready."""
            print(f"Discord bot logged in as {self.bot.user}")
            print(f"Connected to {len(self.bot.guilds)} server(s)")
            # Sync slash commands
            try:
                synced = await self.bot.tree.sync()
                print(f"Synced {len(synced)} slash commands")
            except Exception as e:
                print(f"Failed to sync commands: {e}")

        @self.bot.event
        async def on_message(message):
            """Handle incoming messages."""
            # Ignore bot's own messages
            if message.author == self.bot.user:
                return

            # Check if bot was mentioned
            if self.bot.user in message.mentions:
                question = message.content.replace(f'<@{self.bot.user.id}>', '').strip()
                if question:
                    project_id = self._get_project_id(message.guild)
                    await self._answer_question(message.channel, question, project_id)

            # Handle file uploads
            if message.attachments:
                for attachment in message.attachments:
                    if any(attachment.filename.lower().endswith(ext) for ext in ['.txt', '.md', '.pdf']):
                        # Check if user is admin
                        if message.author.guild_permissions.administrator:
                            await self._handle_file_upload(message, attachment)

        # ============ SLASH COMMANDS ============

        @self.bot.tree.command(name="ask", description="Ask DocBot a question")
        @app_commands.describe(question="Your question")
        async def ask_command(interaction: discord.Interaction, question: str):
            """Ask DocBot a question."""
            await interaction.response.defer()
            project_id = self._get_project_id(interaction.guild)
            await self._answer_interaction(interaction, question, project_id)

        @self.bot.tree.command(name="status", description="Check DocBot status")
        async def status_command(interaction: discord.Interaction):
            """Check DocBot status."""
            project_id = self._get_project_id(interaction.guild)
            server_doc_count = self.vector_store.count(project_id)

            embed = discord.Embed(
                title="DocBot Status",
                color=discord.Color.green()
            )
            embed.add_field(name="Server Docs", value=server_doc_count, inline=True)
            embed.add_field(name="Model", value=config.LLM_MODEL.split('/')[-1], inline=True)
            embed.add_field(name="Status", value="Online", inline=True)
            embed.set_footer(text=f"Server ID: {project_id}")

            await interaction.response.send_message(embed=embed)

        @self.bot.tree.command(name="help", description="Show DocBot help")
        async def help_command(interaction: discord.Interaction):
            """Show DocBot help."""
            embed = discord.Embed(
                title="DocBot Help",
                description="I answer questions based on project documentation!",
                color=discord.Color.blue()
            )
            embed.add_field(
                name="User Commands",
                value="""
`/ask <question>` - Ask a question
`/status` - Check bot status
`@DocBot <question>` - Mention me with a question
                """,
                inline=False
            )
            embed.add_field(
                name="Admin Commands",
                value="""
`/docs_info` - Show loaded docs info
`/load_url <url>` - Load docs from URL
`/load_text <text>` - Add text to knowledge base
`/clear_docs` - Clear all docs for this server
Upload a file (.txt, .md, .pdf) to add docs
                """,
                inline=False
            )

            await interaction.response.send_message(embed=embed)

        @self.bot.tree.command(name="docs_info", description="Show loaded docs info (Admin)")
        @app_commands.default_permissions(administrator=True)
        async def docs_info_command(interaction: discord.Interaction):
            """Show document info for this server."""
            project_id = self._get_project_id(interaction.guild)
            doc_count = self.vector_store.count(project_id)

            embed = discord.Embed(
                title="Documentation Info",
                color=discord.Color.blue()
            )
            embed.add_field(name="Server ID", value=project_id, inline=False)
            embed.add_field(name="Documents Loaded", value=doc_count, inline=True)

            # Get sources if any
            project_docs = [d for d in self.vector_store.documents if d.get("project_id") == project_id]
            sources = list(set(d.get("source", "unknown") for d in project_docs))
            if sources:
                embed.add_field(name="Sources", value="\n".join(sources[:5]), inline=False)

            await interaction.response.send_message(embed=embed)

        @self.bot.tree.command(name="load_url", description="Load docs from URL (Admin)")
        @app_commands.describe(url="The URL to load documentation from")
        @app_commands.default_permissions(administrator=True)
        async def load_url_command(interaction: discord.Interaction, url: str):
            """Load documentation from a URL."""
            await interaction.response.defer()
            project_id = self._get_project_id(interaction.guild)

            try:
                chunks = self.ingester.load_url(url)
                if chunks:
                    self.vector_store.add_documents(chunks, project_id=project_id)
                    await interaction.followup.send(f"Loaded {len(chunks)} chunks from {url}")
                else:
                    await interaction.followup.send("Could not extract any content from that URL.")
            except Exception as e:
                await interaction.followup.send(f"Error loading URL: {e}")

        @self.bot.tree.command(name="load_text", description="Add text to knowledge base (Admin)")
        @app_commands.describe(text="The text to add to the knowledge base")
        @app_commands.default_permissions(administrator=True)
        async def load_text_command(interaction: discord.Interaction, text: str):
            """Load documentation from text directly."""
            project_id = self._get_project_id(interaction.guild)

            try:
                chunks = self.ingester.load_text(text, source="discord_input")
                self.vector_store.add_documents(chunks, project_id=project_id)
                await interaction.response.send_message(f"Added {len(chunks)} chunks to knowledge base!")
            except Exception as e:
                await interaction.response.send_message(f"Error: {e}")

        @self.bot.tree.command(name="clear_docs", description="Clear all docs for this server (Admin)")
        @app_commands.default_permissions(administrator=True)
        async def clear_docs_command(interaction: discord.Interaction):
            """Clear all documents for this server."""
            project_id = self._get_project_id(interaction.guild)
            removed = self.vector_store.clear_project(project_id)
            await interaction.response.send_message(f"Cleared {removed} documents for this server.")

    async def _handle_file_upload(self, message, attachment):
        """Handle file upload from message."""
        project_id = self._get_project_id(message.guild)
        await message.channel.send(f"Processing {attachment.filename}...")

        try:
            # Download file
            file_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "temp", attachment.filename)
            os.makedirs(os.path.dirname(file_path), exist_ok=True)

            async with aiohttp.ClientSession() as session:
                async with session.get(attachment.url) as resp:
                    if resp.status == 200:
                        with open(file_path, 'wb') as f:
                            f.write(await resp.read())

            # Load and process
            chunks = self.ingester.load_file(file_path)
            if chunks:
                self.vector_store.add_documents(chunks, project_id=project_id)
                await message.channel.send(f"Loaded {len(chunks)} chunks from {attachment.filename}")
            else:
                await message.channel.send("Could not extract any content from that file.")

            # Cleanup
            os.remove(file_path)

        except Exception as e:
            logger.error(f"Error processing file: {e}")
            await message.channel.send(f"Error processing file: {e}")

    async def _answer_question(self, channel, question: str, project_id: str = "default"):
        """Generate and send an answer to a channel."""
        async with channel.typing():
            try:
                result = self.answerer.answer(question, project_id=project_id)

                embed = discord.Embed(
                    description=result['answer'],
                    color=discord.Color.blue()
                )

                if result['sources'] and result['confidence'] > 0.5:
                    sources = ', '.join(result['sources'][:3])
                    embed.set_footer(text=f"Source: {sources}")

                await channel.send(embed=embed)

            except Exception as e:
                logger.error(f"Error answering question: {e}")
                await channel.send("Sorry, I encountered an error. Please try again!")

    async def _answer_interaction(self, interaction: discord.Interaction, question: str, project_id: str = "default"):
        """Generate and send an answer to an interaction."""
        try:
            result = self.answerer.answer(question, project_id=project_id)

            embed = discord.Embed(
                description=result['answer'],
                color=discord.Color.blue()
            )

            if result['sources'] and result['confidence'] > 0.5:
                sources = ', '.join(result['sources'][:3])
                embed.set_footer(text=f"Source: {sources}")

            await interaction.followup.send(embed=embed)

        except Exception as e:
            logger.error(f"Error answering question: {e}")
            await interaction.followup.send("Sorry, I encountered an error. Please try again!")

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
