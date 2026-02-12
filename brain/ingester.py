"""
Document Ingester
Loads documents from various sources and chunks them for embedding.
"""

import os
from typing import List, Dict
import httpx

# Add parent directory to path for imports
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import config


class DocumentIngester:
    """Loads and chunks documents for the vector database."""

    def __init__(self, chunk_size: int = None, chunk_overlap: int = None):
        self.chunk_size = chunk_size or config.CHUNK_SIZE
        self.chunk_overlap = chunk_overlap or config.CHUNK_OVERLAP

    def load_text(self, text: str, source: str = "direct_input") -> List[Dict]:
        """
        Load text directly and chunk it.

        Args:
            text: The text content to process
            source: Identifier for where this text came from

        Returns:
            List of chunks with metadata
        """
        chunks = self._chunk_text(text)
        return [
            {
                "text": chunk,
                "source": source,
                "chunk_index": i
            }
            for i, chunk in enumerate(chunks)
        ]

    def load_file(self, file_path: str) -> List[Dict]:
        """
        Load a file and chunk it.

        Supports: .txt, .md, .pdf

        Args:
            file_path: Path to the file

        Returns:
            List of chunks with metadata
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")

        ext = os.path.splitext(file_path)[1].lower()

        if ext in [".txt", ".md"]:
            with open(file_path, "r", encoding="utf-8") as f:
                text = f.read()
        elif ext == ".pdf":
            text = self._load_pdf(file_path)
        else:
            raise ValueError(f"Unsupported file type: {ext}")

        return self.load_text(text, source=os.path.basename(file_path))

    def load_url(self, url: str) -> List[Dict]:
        """
        Fetch content from a URL and chunk it.

        Args:
            url: The URL to fetch

        Returns:
            List of chunks with metadata
        """
        try:
            response = httpx.get(url, follow_redirects=True, timeout=30)
            response.raise_for_status()
            text = response.text

            # Basic HTML stripping (simple approach)
            if "<html" in text.lower():
                text = self._strip_html(text)

            return self.load_text(text, source=url)
        except Exception as e:
            raise RuntimeError(f"Failed to fetch URL: {e}")

    def load_directory(self, dir_path: str, extensions: List[str] = None) -> List[Dict]:
        """
        Load all documents from a directory.

        Args:
            dir_path: Path to the directory
            extensions: List of file extensions to include (e.g., [".txt", ".md"])

        Returns:
            List of all chunks from all files
        """
        if extensions is None:
            extensions = [".txt", ".md", ".pdf"]

        all_chunks = []

        for filename in os.listdir(dir_path):
            ext = os.path.splitext(filename)[1].lower()
            if ext in extensions:
                file_path = os.path.join(dir_path, filename)
                try:
                    chunks = self.load_file(file_path)
                    all_chunks.extend(chunks)
                    print(f"Loaded: {filename} ({len(chunks)} chunks)")
                except Exception as e:
                    print(f"Error loading {filename}: {e}")

        return all_chunks

    def _chunk_text(self, text: str) -> List[str]:
        """
        Split text into overlapping chunks.

        Args:
            text: The text to chunk

        Returns:
            List of text chunks
        """
        # Clean up the text
        text = text.strip()

        if len(text) <= self.chunk_size:
            return [text] if text else []

        chunks = []
        start = 0

        while start < len(text):
            # Get chunk
            end = start + self.chunk_size

            # Try to break at a sentence or word boundary
            if end < len(text):
                # Look for sentence break
                for sep in [". ", ".\n", "\n\n", "\n", " "]:
                    last_sep = text[start:end].rfind(sep)
                    if last_sep != -1 and last_sep > self.chunk_size // 2:
                        end = start + last_sep + len(sep)
                        break

            chunk = text[start:end].strip()
            if chunk:
                chunks.append(chunk)

            # Move start position with overlap
            start = end - self.chunk_overlap

        return chunks

    def _load_pdf(self, file_path: str) -> str:
        """Load text from a PDF file."""
        try:
            from pypdf import PdfReader
            reader = PdfReader(file_path)
            text = ""
            for page in reader.pages:
                text += page.extract_text() + "\n"
            return text
        except ImportError:
            raise ImportError("pypdf is required for PDF support. Install with: pip install pypdf")

    def _strip_html(self, html: str) -> str:
        """Basic HTML tag stripping."""
        import re
        # Remove script and style elements
        html = re.sub(r'<script[^>]*>.*?</script>', '', html, flags=re.DOTALL | re.IGNORECASE)
        html = re.sub(r'<style[^>]*>.*?</style>', '', html, flags=re.DOTALL | re.IGNORECASE)
        # Remove HTML tags
        html = re.sub(r'<[^>]+>', ' ', html)
        # Clean up whitespace
        html = re.sub(r'\s+', ' ', html)
        return html.strip()


# =============================================================================
# Quick Test
# =============================================================================

if __name__ == "__main__":
    ingester = DocumentIngester()

    # Test with sample text
    sample_text = """
    Welcome to CryptoProject!

    CryptoProject is a decentralized protocol for earning yield on your crypto assets.

    How to stake:
    1. Connect your wallet
    2. Select the amount to stake
    3. Confirm the transaction
    4. Start earning rewards!

    Tokenomics:
    - Total supply: 100,000,000 tokens
    - Staking rewards: 10% APY
    - Team allocation: 15%

    For more information, visit our docs at docs.cryptoproject.io
    """

    chunks = ingester.load_text(sample_text, source="test")

    print(f"\nChunked into {len(chunks)} pieces:")
    for i, chunk in enumerate(chunks):
        print(f"\n--- Chunk {i + 1} ---")
        print(f"Source: {chunk['source']}")
        print(f"Text: {chunk['text'][:100]}...")
