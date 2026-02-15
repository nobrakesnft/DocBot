"""
Discord Bot Connector
Handles Discord-specific message handling using the shared brain.
Self-explanatory UX - anyone can use it without coding knowledge.
"""

import os
import sys
import logging
import aiohttp
import asyncio

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import discord
from discord import app_commands
from discord.ext import commands

import config
from brain import DocumentIngester, VectorStore, Answerer
from connectors import bot_utils

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

    def _get_doc_count(self, project_id: str) -> int:
        """Get document count for a project."""
        return self.vector_store.count(project_id)

    def _get_suggested_questions(self) -> str:
        """Return suggested questions text."""
        return """
💡 **Try asking:**
• "How do I get started?"
• "What are the tokenomics?"
• "How does staking work?"
• Or ask anything about the project!"""

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
        async def on_guild_join(guild):
            """Send welcome message when bot joins a new server."""
            # Find the first text channel we can send to
            channel = None
            for ch in guild.text_channels:
                if ch.permissions_for(guild.me).send_messages:
                    channel = ch
                    break

            if channel:
                embed = discord.Embed(
                    title="👋 Hey! I'm DocBot!",
                    description="I answer questions based on your project's documentation, so your community gets instant help 24/7.",
                    color=discord.Color.blue()
                )
                embed.add_field(
                    name="🚀 Quick Setup (Admins)",
                    value="1️⃣ Upload a doc file (.txt, .md, .pdf)\n2️⃣ Or use `/load_url https://your-docs.com`\n\nOnce docs are loaded, anyone can ask questions!",
                    inline=False
                )
                embed.add_field(
                    name="❓ Ask Questions",
                    value="Use `/ask <question>` or @mention me!\n\nExample: `/ask How do I stake?`",
                    inline=False
                )
                embed.add_field(
                    name="📚 Need Help?",
                    value="Type `/help` for all commands",
                    inline=False
                )
                embed.set_footer(text="Part of ChainPilot - AI agents for Web3 communities")

                await channel.send(embed=embed)

        @self.bot.event
        async def on_message(message):
            """Handle incoming messages."""
            # Ignore bot's own messages
            if message.author == self.bot.user:
                return

            # Check if bot was mentioned
            if self.bot.user in message.mentions:
                question = message.content.replace(f'<@{self.bot.user.id}>', '').strip()

                # Just mentioned without text - casual response
                if not question:
                    await message.reply("yo, got a question? just @ me with it", mention_author=False)
                    return

                # Check if it should be ignored (greetings, reactions, etc.)
                if bot_utils.should_ignore(question):
                    # Maybe respond to greetings casually
                    if bot_utils.is_greeting(question):
                        greetings = ["gm!", "hey 👋", "yo", "gm gm"]
                        import random
                        await message.reply(random.choice(greetings), mention_author=False)
                    return

                # When explicitly @tagged, skip is_question() check
                # Let the LLM handle it - it will answer or ask for clarification naturally

                # Rate limiting
                user_id = str(message.author.id)
                is_allowed, remaining = bot_utils.check_cooldown(user_id)
                if not is_allowed:
                    await message.reply(f"chill, gimme like {remaining}s 😅", mention_author=False)
                    return

                # Answer the question
                project_id = self._get_project_id(message.guild)
                await self._answer_question(message, question, project_id)
                bot_utils.record_question(user_id)

            # Handle file uploads from admins
            if message.attachments:
                for attachment in message.attachments:
                    if any(attachment.filename.lower().endswith(ext) for ext in ['.txt', '.md', '.pdf']):
                        # Check if user is admin
                        if message.author.guild_permissions.administrator:
                            await self._handle_file_upload(message, attachment)

        # ============ SLASH COMMANDS ============

        @self.bot.tree.command(name="ask", description="❓ Ask DocBot a question about the project")
        @app_commands.describe(question="Your question about the project")
        async def ask_command(interaction: discord.Interaction, question: str):
            """Ask DocBot a question."""
            await interaction.response.defer()
            project_id = self._get_project_id(interaction.guild)
            await self._answer_interaction(interaction, question, project_id)

        @self.bot.tree.command(name="status", description="📊 Check DocBot status and loaded docs")
        async def status_command(interaction: discord.Interaction):
            """Check DocBot status."""
            project_id = self._get_project_id(interaction.guild)
            doc_count = self._get_doc_count(project_id)

            if doc_count > 0:
                embed = discord.Embed(
                    title="✅ DocBot is Ready!",
                    color=discord.Color.green()
                )
                embed.add_field(name="📊 Documents", value=f"{doc_count} chunks loaded", inline=True)
                embed.add_field(name="🤖 AI Model", value=config.LLM_MODEL.split('/')[-1], inline=True)
                embed.add_field(name="💬 Status", value="Online", inline=True)
                embed.add_field(
                    name="❓ Ask a Question",
                    value="Use `/ask <question>` or @mention me!",
                    inline=False
                )
            else:
                embed = discord.Embed(
                    title="⚠️ No Documents Loaded",
                    description="I need documentation to answer questions!",
                    color=discord.Color.yellow()
                )
                embed.add_field(
                    name="🚀 Quick Setup (Admins)",
                    value="1️⃣ Upload a doc file (.txt, .md, .pdf)\n2️⃣ Or use `/load_url https://your-docs.com`",
                    inline=False
                )

            await interaction.response.send_message(embed=embed)

        @self.bot.tree.command(name="help", description="📚 Show all DocBot commands")
        async def help_command(interaction: discord.Interaction):
            """Show DocBot help."""
            project_id = self._get_project_id(interaction.guild)
            doc_count = self._get_doc_count(project_id)

            embed = discord.Embed(
                title="📚 DocBot Help",
                description="I answer questions based on project documentation!",
                color=discord.Color.blue()
            )
            embed.add_field(
                name="━━━ FOR EVERYONE ━━━",
                value="`/ask <question>` - Ask a question\n`/status` - Check bot status\n`@DocBot <question>` - Mention me with a question",
                inline=False
            )
            embed.add_field(
                name="━━━ FOR ADMINS ━━━",
                value="**Adding Docs:**\n• Upload a file (.txt, .md, .pdf)\n• `/load_url <link>` - Load from website\n• `/load_text <text>` - Add text directly\n\n**Management:**\n• `/docs_info` - See what's loaded\n• `/clear_docs` - Start fresh",
                inline=False
            )
            embed.add_field(
                name="━━━ EXAMPLES ━━━",
                value='"/ask How do I stake my tokens?"\n"/ask What wallets are supported?"\n"/ask What is the max supply?"',
                inline=False
            )
            embed.set_footer(text=f"📊 Currently loaded: {doc_count} document chunks")

            await interaction.response.send_message(embed=embed)

        @self.bot.tree.command(name="setup", description="🚀 Quick setup guide for admins")
        @app_commands.default_permissions(administrator=True)
        async def setup_command(interaction: discord.Interaction):
            """Guided onboarding for admins."""
            project_id = self._get_project_id(interaction.guild)
            doc_count = self._get_doc_count(project_id)

            if doc_count > 0:
                # Already set up
                embed = discord.Embed(
                    title="✅ DocBot is Ready!",
                    description=f"**{doc_count}** doc chunks loaded and ready to answer questions.",
                    color=discord.Color.green()
                )
                embed.add_field(
                    name="🔧 Quick Actions",
                    value="• `/docs_info` - See what's loaded\n• `/load_url <link>` - Add more docs\n• `/clear_docs` - Start fresh",
                    inline=False
                )
                embed.add_field(
                    name="🧪 Test It",
                    value="Try: `/ask How do I get started?`",
                    inline=False
                )
            else:
                # Fresh setup
                embed = discord.Embed(
                    title="🚀 Let's Set Up DocBot!",
                    description="Get your AI support bot running in 3 steps.",
                    color=discord.Color.blue()
                )
                embed.add_field(
                    name="Step 1️⃣ Add Your Docs",
                    value="Choose one:\n📄 Upload a file (.txt, .md, .pdf)\n🔗 `/load_url https://your-docs.com`\n📝 `/load_text <paste FAQ here>`",
                    inline=False
                )
                embed.add_field(
                    name="Step 2️⃣ Test It",
                    value="Ask: `/ask How do I stake?`",
                    inline=False
                )
                embed.add_field(
                    name="Step 3️⃣ Done!",
                    value="Your community can now ask questions 24/7 ✨",
                    inline=False
                )
                embed.add_field(
                    name="💡 Pro Tips",
                    value="• Upload whitepaper, FAQ, or gitbook\n• More docs = better answers\n• Bot learns from what you upload",
                    inline=False
                )

            await interaction.response.send_message(embed=embed)

        @self.bot.tree.command(name="docs_info", description="📄 Show loaded documentation info (Admin)")
        @app_commands.default_permissions(administrator=True)
        async def docs_info_command(interaction: discord.Interaction):
            """Show document info for this server."""
            project_id = self._get_project_id(interaction.guild)
            doc_count = self._get_doc_count(project_id)

            if doc_count == 0:
                embed = discord.Embed(
                    title="📭 No Documents Loaded",
                    description="To add docs:\n• Upload a file (.txt, .md, .pdf)\n• Or use `/load_url https://your-docs.com`",
                    color=discord.Color.yellow()
                )
                await interaction.response.send_message(embed=embed)
                return

            # Get sources
            project_docs = [d for d in self.vector_store.documents if d.get("project_id") == project_id]
            sources = list(set(d.get("source", "unknown") for d in project_docs))

            embed = discord.Embed(
                title="📚 Documentation Info",
                color=discord.Color.blue()
            )
            embed.add_field(name="📊 Total Chunks", value=str(doc_count), inline=True)
            embed.add_field(name="📄 Sources", value=str(len(sources)), inline=True)

            sources_text = "\n".join(f"• {s}" for s in sources[:5])
            if len(sources) > 5:
                sources_text += f"\n• ... and {len(sources) - 5} more"
            embed.add_field(name="📁 Source Files", value=sources_text or "Unknown", inline=False)
            embed.add_field(name="✅ Status", value="Ready to answer questions!", inline=False)

            await interaction.response.send_message(embed=embed)

        @self.bot.tree.command(name="load_url", description="🔗 Load documentation from a URL (Admin)")
        @app_commands.describe(url="The URL to load documentation from")
        @app_commands.default_permissions(administrator=True)
        async def load_url_command(interaction: discord.Interaction, url: str):
            """Load documentation from a URL."""
            await interaction.response.defer()
            project_id = self._get_project_id(interaction.guild)

            # Send loading message
            await interaction.followup.send(f"🔄 Loading docs from URL...\n{url}")

            try:
                chunks = self.ingester.load_url(url)
                if chunks:
                    self.vector_store.add_documents(chunks, project_id=project_id)
                    total_docs = self._get_doc_count(project_id)

                    embed = discord.Embed(
                        title="✅ Documentation Loaded!",
                        color=discord.Color.green()
                    )
                    embed.add_field(name="📥 Chunks Added", value=str(len(chunks)), inline=True)
                    embed.add_field(name="📊 Total Docs", value=str(total_docs), inline=True)
                    embed.add_field(name="🔗 Source", value=url[:50] + "..." if len(url) > 50 else url, inline=False)
                    embed.add_field(
                        name="✅ Ready!",
                        value="I can now answer questions about this content!\n\nTry: `/ask How do I get started?`",
                        inline=False
                    )

                    await interaction.channel.send(embed=embed)
                else:
                    await interaction.channel.send(
                        "⚠️ Couldn't extract content from that URL.\n\n"
                        "Try a different page, or use `/load_text` to paste content directly."
                    )
            except Exception as e:
                await interaction.channel.send(f"❌ Error loading URL: {e}\n\nMake sure the URL is correct and accessible.")

        @self.bot.tree.command(name="load_text", description="📝 Add text to knowledge base (Admin)")
        @app_commands.describe(text="The text to add to the knowledge base")
        @app_commands.default_permissions(administrator=True)
        async def load_text_command(interaction: discord.Interaction, text: str):
            """Load documentation from text directly."""
            project_id = self._get_project_id(interaction.guild)

            try:
                chunks = self.ingester.load_text(text, source="manual_input")
                self.vector_store.add_documents(chunks, project_id=project_id)
                total_docs = self._get_doc_count(project_id)

                embed = discord.Embed(
                    title="✅ Text Added!",
                    color=discord.Color.green()
                )
                embed.add_field(name="📥 Chunks Added", value=str(len(chunks)), inline=True)
                embed.add_field(name="📊 Total Docs", value=str(total_docs), inline=True)
                embed.add_field(
                    name="✅ Ready!",
                    value="I can now answer questions about this content!",
                    inline=False
                )

                await interaction.response.send_message(embed=embed)
            except Exception as e:
                await interaction.response.send_message(f"❌ Error adding text: {e}")

        @self.bot.tree.command(name="clear_docs", description="🗑️ Clear all docs for this server (Admin)")
        @app_commands.default_permissions(administrator=True)
        async def clear_docs_command(interaction: discord.Interaction):
            """Clear all documents for this server."""
            project_id = self._get_project_id(interaction.guild)
            doc_count = self._get_doc_count(project_id)

            if doc_count == 0:
                await interaction.response.send_message("📭 No documents to clear!")
                return

            removed = self.vector_store.clear_project(project_id)

            embed = discord.Embed(
                title="🗑️ Documents Cleared",
                description=f"Removed {removed} document chunks.",
                color=discord.Color.orange()
            )
            embed.add_field(
                name="📄 Add New Docs",
                value="• Upload a file (.txt, .md, .pdf)\n• Or use `/load_url https://your-docs.com`",
                inline=False
            )

            await interaction.response.send_message(embed=embed)

        @self.bot.tree.command(name="set_tone", description="🎨 Set bot response tone (Admin)")
        @app_commands.describe(tone="Response tone: casual, neutral, or professional")
        @app_commands.choices(tone=[
            app_commands.Choice(name="casual - Friendly, web3-native, light slang", value="casual"),
            app_commands.Choice(name="neutral - Friendly but clean, no slang", value="neutral"),
            app_commands.Choice(name="professional - Formal support tone", value="professional"),
        ])
        @app_commands.default_permissions(administrator=True)
        async def set_tone_command(interaction: discord.Interaction, tone: str):
            """Set the response tone for this server."""
            project_id = self._get_project_id(interaction.guild)

            if bot_utils.set_project_tone(project_id, tone):
                tone_descriptions = {
                    "casual": "Friendly, web3-native, light slang allowed 🤙",
                    "neutral": "Friendly but clean, no slang or emojis",
                    "professional": "Formal support tone, precise language",
                }

                embed = discord.Embed(
                    title="🎨 Tone Updated!",
                    color=discord.Color.green()
                )
                embed.add_field(name="New Tone", value=f"**{tone}**", inline=True)
                embed.add_field(name="Style", value=tone_descriptions[tone], inline=False)

                # Show example
                examples = {
                    "casual": '"No exact date yet, snapshot is planned for Q2 2026 👀"',
                    "neutral": '"Snapshot is planned for Q2 2026, but no exact date has been announced yet."',
                    "professional": '"The snapshot is scheduled for Q2 2026. An exact date has not yet been announced."',
                }
                embed.add_field(name="Example Response", value=examples[tone], inline=False)

                await interaction.response.send_message(embed=embed)
            else:
                await interaction.response.send_message(
                    "❌ Invalid tone. Choose: casual, neutral, or professional"
                )

    async def _handle_file_upload(self, message, attachment):
        """Handle file upload from message."""
        project_id = self._get_project_id(message.guild)

        # Check file extension
        file_name = attachment.filename.lower()
        supported = ['.txt', '.md', '.pdf']
        if not any(file_name.endswith(ext) for ext in supported):
            await message.channel.send(
                f"⚠️ Unsupported file format!\n\n"
                f"Supported: {', '.join(supported)}\n"
                f"You uploaded: {attachment.filename}"
            )
            return

        await message.channel.send(f"📄 Processing {attachment.filename}...")

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
                total_docs = self._get_doc_count(project_id)

                embed = discord.Embed(
                    title="✅ Documentation Loaded!",
                    color=discord.Color.green()
                )
                embed.add_field(name="📄 File", value=attachment.filename, inline=True)
                embed.add_field(name="📥 Chunks", value=str(len(chunks)), inline=True)
                embed.add_field(name="📊 Total", value=str(total_docs), inline=True)
                embed.add_field(
                    name="✅ Ready!",
                    value="I can now answer questions about this content!\n\nTry: `/ask How do I get started?`",
                    inline=False
                )

                await message.channel.send(embed=embed)
            else:
                await message.channel.send(
                    f"⚠️ Couldn't extract content from {attachment.filename}.\n\n"
                    "The file might be empty or in an unsupported format."
                )

            # Cleanup
            os.remove(file_path)

        except Exception as e:
            logger.error(f"Error processing file: {e}")
            await message.channel.send(f"❌ Error processing file: {e}")

    async def _answer_question(self, message, question: str, project_id: str = "default"):
        """
        Generate and send an answer with proper duplicate/spam control.

        Flow:
        1. Check docs loaded
        2. Check for cached duplicate (includes link to original)
        3. If duplicate: send sassy response with link
        4. If allowed: generate answer, cache it
        """
        channel_id = str(message.channel.id)
        user_id = str(message.author.id)
        doc_count = self._get_doc_count(project_id)

        # Step 1: Check if docs are loaded
        if doc_count == 0:
            await message.reply(
                "no docs loaded yet - an admin needs to upload a file or use `/load_url` first",
                mention_author=False
            )
            return

        # Step 2: Check for cached duplicate answer
        cached = bot_utils.find_cached_answer(question, project_id)
        if cached:
            # Extract topic for contextual response
            topic = bot_utils.extract_topic(question)

            # Track repeat count per channel+topic
            cache_key = f"{channel_id}:{topic}"
            repeat_count = bot_utils.get_repeat_count(cache_key)

            # Get sassy response with topic
            response = bot_utils.get_smart_duplicate_response(topic, repeat_count)

            if response:
                # Include link to original answer
                await message.reply(f"{response}\n{cached['message_ref']}", mention_author=False)
            # If None, stay silent
            return

        # Step 3: Generate fresh answer
        async with message.channel.typing():
            await bot_utils.human_typing_delay()

            try:
                result = self.answerer.answer(question, project_id=project_id)

                # Send answer
                reply_msg = await message.reply(result['answer'], mention_author=False)

                # Cache the answer for duplicate detection
                message_link = f"https://discord.com/channels/{message.guild.id}/{message.channel.id}/{reply_msg.id}"
                bot_utils.cache_answer(
                    question=question,
                    answer=result['answer'],
                    project_id=project_id,
                    message_ref=message_link,
                    user_id=user_id
                )

            except Exception as e:
                logger.error(f"Error answering question: {e}")
                await message.reply("something went wrong, try again?", mention_author=False)

    async def _answer_interaction(self, interaction: discord.Interaction, question: str, project_id: str = "default"):
        """Generate and send an answer to an interaction (slash command)."""
        channel_id = str(interaction.channel.id)
        user_id = str(interaction.user.id)
        doc_count = self._get_doc_count(project_id)

        # Step 1: Check if docs are loaded
        if doc_count == 0:
            await interaction.followup.send(
                "no docs loaded yet - an admin needs to upload a file or use `/load_url` first"
            )
            return

        # Step 2: Rate limiting
        is_allowed, remaining = bot_utils.check_cooldown(user_id)
        if not is_allowed:
            await interaction.followup.send(f"chill, gimme like {remaining}s 😅")
            return

        # Step 3: Check for cached duplicate answer
        cached = bot_utils.find_cached_answer(question, project_id)
        if cached:
            topic = bot_utils.extract_topic(question)
            cache_key = f"{channel_id}:{topic}"
            repeat_count = bot_utils.get_repeat_count(cache_key)

            response = bot_utils.get_smart_duplicate_response(topic, repeat_count)
            if response:
                await interaction.followup.send(f"{response}\n{cached['message_ref']}")
            return

        try:
            result = self.answerer.answer(question, project_id=project_id)

            # Plain text reply
            reply_msg = await interaction.followup.send(result['answer'], wait=True)
            bot_utils.record_question(user_id)

            # Cache the answer
            message_link = f"https://discord.com/channels/{interaction.guild.id}/{interaction.channel.id}/{reply_msg.id}"
            bot_utils.cache_answer(
                question=question,
                answer=result['answer'],
                project_id=project_id,
                message_ref=message_link,
                user_id=user_id
            )

        except Exception as e:
            logger.error(f"Error answering question: {e}")
            error_responses = [
                "ah something went wrong, try again?",
                "oops hit an error there, mind rephrasing?",
                "hmm broke something, try again maybe?",
            ]
            await interaction.followup.send(random.choice(error_responses))

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
