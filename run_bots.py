"""
Run both Telegram and Discord bots simultaneously.
Used for production deployment on Railway.
"""

import os
import sys
import threading
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import config

# Import bots at top level to avoid threading deadlock
from connectors.telegram_bot import TelegramBot
from connectors.discord_bot import DiscordBot


def run_telegram_bot():
    """Run Telegram bot in a thread."""
    print("Starting Telegram bot...")
    bot = TelegramBot()
    bot.run()


def run_discord_bot():
    """Run Discord bot in a thread."""
    print("Starting Discord bot...")
    bot = DiscordBot()
    bot.run()


def main():
    """Run both bots based on available tokens."""
    print("=" * 50)
    print("DocBot - Starting Production Server")
    print("=" * 50)

    # Check which bots we can run
    has_telegram = config.TELEGRAM_BOT_TOKEN and config.TELEGRAM_BOT_TOKEN != "your_telegram_bot_token_here"
    has_discord = config.DISCORD_BOT_TOKEN and config.DISCORD_BOT_TOKEN != "your_discord_bot_token_here"

    if not has_telegram and not has_discord:
        print("\nERROR: No bot tokens configured!")
        print("Set TELEGRAM_BOT_TOKEN and/or DISCORD_BOT_TOKEN in environment variables.")
        sys.exit(1)

    threads = []

    if has_telegram:
        print("Telegram token found")
        t = threading.Thread(target=run_telegram_bot, daemon=True, name="TelegramBot")
        threads.append(t)
    else:
        print("Telegram token not set - skipping")

    if has_discord:
        print("Discord token found")
        t = threading.Thread(target=run_discord_bot, daemon=True, name="DiscordBot")
        threads.append(t)
    else:
        print("Discord token not set - skipping")

    print(f"\nStarting {len(threads)} bot(s)...")
    print("-" * 50)

    # Start all threads
    for t in threads:
        t.start()
        time.sleep(2)  # Stagger starts to avoid race conditions

    # Keep main thread alive
    try:
        while True:
            # Check if any thread died
            alive = [t for t in threads if t.is_alive()]
            if not alive:
                print("All bots stopped!")
                break
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nShutting down...")


if __name__ == "__main__":
    main()
