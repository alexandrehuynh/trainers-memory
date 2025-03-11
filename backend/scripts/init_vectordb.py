#!/usr/bin/env python
"""
Initialize Vector Database Script

This script initializes the vector database with fitness domain knowledge.
It should be run once before using the RAG features.

Usage:
    python init_vectordb.py [--force]

Options:
    --force    Force recreation of the vector database even if it exists
"""

import os
import sys
import argparse
from dotenv import load_dotenv

# Add the parent directory to the path so we can import app modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Load environment variables
load_dotenv()

# Import after path setup
from app.utils.fitness_data.embedding_tools import create_fitness_embeddings
from app.utils.vectordb import get_vectordb

def main():
    """Initialize the vector database with fitness knowledge."""
    # Parse arguments
    parser = argparse.ArgumentParser(description='Initialize the vector database with fitness knowledge.')
    parser.add_argument('--force', action='store_true', help='Force recreation of the vector database')
    args = parser.parse_args()
    
    print("Initializing vector database...")
    
    # Get vector database
    vectordb = get_vectordb()
    
    # Check if database already exists
    if len(vectordb.metadata) > 0 and not args.force:
        print(f"Vector database already contains {len(vectordb.metadata)} entries.")
        print("Use --force to recreate the database.")
        return
    
    # Create embeddings
    counts = create_fitness_embeddings(force_refresh=args.force)
    
    # Print results
    print("\nVector database initialization complete!")
    print(f"Total entries: {sum(counts.values())}")
    print("Entries by category:")
    for category, count in counts.items():
        print(f"  - {category}: {count}")
    
    # Print stats
    stats = vectordb.get_stats()
    print(f"\nEmbedding model: {stats['embedding_model']}")
    print(f"Embedding dimension: {stats['embedding_dimension']}")

if __name__ == '__main__':
    main() 