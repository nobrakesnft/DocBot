"""
DocBot Brain Module
Contains the AI logic: document ingestion, vector search, and answer generation.
"""

from .ingester import DocumentIngester
from .vectorstore import VectorStore
from .answerer import Answerer

__all__ = ["DocumentIngester", "VectorStore", "Answerer"]
