"""
DocBot - AI Community Support Bot
Main entry point for running the bots.

Usage:
    python main.py telegram    # Run Telegram bot only
    python main.py discord     # Run Discord bot only
    python main.py test        # Test the brain without bots
    python main.py ingest      # Load documents into vector store
"""

import os
import sys
import argparse

# Ensure we can import from project root
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import config
from brain import DocumentIngester, VectorStore, Answerer


def test_brain():
    """Test the AI brain with sample questions."""
    print("=" * 60)
    print("DocBot Brain Test")
    print("=" * 60)

    # Check config
    errors = config.validate_config()
    if errors:
        print("\nConfiguration errors:")
        for e in errors:
            print(f"  - {e}")
        return

    print(f"\nUsing model: {config.LLM_MODEL}")

    # Initialize components
    store = VectorStore()
    print(f"Documents in store: {store.count()}")

    if store.count() == 0:
        print("\nNo documents loaded. Loading sample...")
        ingester = DocumentIngester()
        sample = """
        Welcome to TestProject!

        How to stake:
        1. Connect wallet at app.testproject.io
        2. Click Stake
        3. Enter amount
        4. Confirm transaction
        5. Earn 10% APY!

        Supported wallets: MetaMask, WalletConnect, Coinbase Wallet
        Minimum stake: 100 tokens
        Unbonding period: 7 days
        """
        chunks = ingester.load_text(sample, "sample_docs")
        store.add_documents(chunks)
        print(f"Loaded {len(chunks)} chunks")

    # Test answerer
    answerer = Answerer(store)

    print("\n" + "-" * 60)
    print("Testing Q&A")
    print("-" * 60)

    questions = [
        "How do I stake?",
        "What wallets can I use?",
        "What is the APY?"
    ]

    for q in questions:
        print(f"\nQ: {q}")
        result = answerer.answer(q)
        print(f"A: {result['answer']}")
        print(f"   Confidence: {result['confidence']:.2f}")


def ingest_documents():
    """Load documents from data/docs directory."""
    print("=" * 60)
    print("Document Ingestion")
    print("=" * 60)

    docs_dir = os.path.join(os.path.dirname(__file__), "data", "docs")

    if not os.path.exists(docs_dir):
        os.makedirs(docs_dir, exist_ok=True)
        print(f"\nCreated docs directory: {docs_dir}")
        print("Please add your documents (.txt, .md, .pdf) to this folder")
        print("Then run: python main.py ingest")
        return

    files = [f for f in os.listdir(docs_dir) if f.endswith(('.txt', '.md', '.pdf'))]

    if not files:
        print(f"\nNo documents found in: {docs_dir}")
        print("Add your .txt, .md, or .pdf files there and try again")
        return

    print(f"\nFound {len(files)} document(s):")
    for f in files:
        print(f"  - {f}")

    # Initialize
    ingester = DocumentIngester()
    store = VectorStore()

    # Clear existing
    print("\nClearing existing documents...")
    try:
        store.clear()
    except:
        pass  # Collection might not exist yet

    # Load new
    print("Loading documents...")
    chunks = ingester.load_directory(docs_dir)

    if chunks:
        store.add_documents(chunks)
        print(f"\nSuccess! Loaded {len(chunks)} chunks from {len(files)} files")
        print(f"Total documents in store: {store.count()}")
    else:
        print("No chunks created. Check your document files.")


def run_telegram():
    """Run the Telegram bot."""
    from connectors.telegram_bot import TelegramBot
    bot = TelegramBot()
    bot.run()


def run_discord():
    """Run the Discord bot."""
    from connectors.discord_bot import DiscordBot
    bot = DiscordBot()
    bot.run()


def main():
    parser = argparse.ArgumentParser(
        description="DocBot - AI Community Support Bot",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python main.py test        Test the AI brain
  python main.py ingest      Load documents from data/docs/
  python main.py telegram    Run Telegram bot
  python main.py discord     Run Discord bot
        """
    )

    parser.add_argument(
        "command",
        choices=["telegram", "discord", "test", "ingest"],
        help="Command to run"
    )

    args = parser.parse_args()

    if args.command == "test":
        test_brain()
    elif args.command == "ingest":
        ingest_documents()
    elif args.command == "telegram":
        run_telegram()
    elif args.command == "discord":
        run_discord()


if __name__ == "__main__":
    if len(sys.argv) == 1:
        # No arguments, show help
        print("""
DocBot - AI Community Support Bot

Usage:
  python main.py test        Test the AI brain
  python main.py ingest      Load documents from data/docs/
  python main.py telegram    Run Telegram bot
  python main.py discord     Run Discord bot

First time? Try:
  1. Add your GROQ_API_KEY to .env
  2. Run: python main.py test
        """)
    else:
        main()
