"""
DocBot Connectors
Platform-specific bot implementations that use the shared brain.
"""

from .telegram_bot import TelegramBot
from .discord_bot import DiscordBot

__all__ = ["TelegramBot", "DiscordBot"]
