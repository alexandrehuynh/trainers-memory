"""
Vector Database Module

This module provides vector database functionality for implementing
Retrieval Augmented Generation (RAG) with fitness domain knowledge.
"""

from .faiss_db import FitnessVectorDB, get_vectordb

__all__ = ['FitnessVectorDB', 'get_vectordb'] 