"""
Fitness Domain Knowledge Module

This module provides domain-specific knowledge about fitness
for use in the vector database and RAG system.
"""

from .knowledge_base import load_fitness_knowledge, get_exercise_info
from .embedding_tools import create_fitness_embeddings

__all__ = ['load_fitness_knowledge', 'get_exercise_info', 'create_fitness_embeddings'] 