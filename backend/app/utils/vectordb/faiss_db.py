"""
FAISS Vector Database Module

This module implements a vector database using FAISS for storing and
retrieving fitness domain knowledge. It supports:

1. Adding fitness knowledge (exercises, techniques, etc.)
2. Searching for similar content using vector embeddings
3. Persisting and loading the vector database
4. Using sentence transformers for creating embeddings

This is used for implementing Retrieval Augmented Generation (RAG) to enhance
LLM responses with domain-specific knowledge.
"""

import os
import json
import pickle
import numpy as np
from typing import List, Dict, Any, Optional, Tuple
import faiss
from sentence_transformers import SentenceTransformer
from datetime import datetime

# Define path for storing the vector database
VECTOR_DB_DIR = os.getenv("VECTOR_DB_DIR", "data/vectordb")
VECTOR_DB_PATH = os.path.join(VECTOR_DB_DIR, "fitness_vectordb.faiss")
METADATA_PATH = os.path.join(VECTOR_DB_DIR, "fitness_metadata.pickle")

# Default embedding model - can be overridden in .env
DEFAULT_EMBEDDING_MODEL = "all-MiniLM-L6-v2"
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", DEFAULT_EMBEDDING_MODEL)

class FitnessVectorDB:
    """FAISS Vector Database for fitness domain knowledge."""
    
    def __init__(self, embedding_model: Optional[str] = None):
        """Initialize the vector database.
        
        Args:
            embedding_model: Name of the sentence transformers model to use
        """
        # Set embedding model
        self.embedding_model_name = embedding_model or EMBEDDING_MODEL
        print(f"Initializing vector database with model: {self.embedding_model_name}")
        
        # Load embedding model
        try:
            self.embedding_model = SentenceTransformer(self.embedding_model_name)
            self.dimension = self.embedding_model.get_sentence_embedding_dimension()
            print(f"Loaded embedding model with dimension: {self.dimension}")
        except Exception as e:
            print(f"Error loading embedding model: {str(e)}")
            # Fall back to a simple model if the specified one fails
            self.embedding_model = SentenceTransformer(DEFAULT_EMBEDDING_MODEL)
            self.dimension = self.embedding_model.get_sentence_embedding_dimension()
            print(f"Loaded fallback embedding model with dimension: {self.dimension}")
        
        # Initialize FAISS index
        self.index = faiss.IndexFlatL2(self.dimension)
        
        # Initialize metadata storage
        self.metadata = []
        
        # Load existing database if available
        self.load_db()
    
    def _create_embedding(self, text: str) -> np.ndarray:
        """Create an embedding vector for the given text.
        
        Args:
            text: Text to embed
            
        Returns:
            Numpy array containing the embedding vector
        """
        return self.embedding_model.encode([text])[0]
    
    def add_knowledge(self, content: str, metadata: Dict[str, Any]) -> int:
        """Add a piece of fitness knowledge to the vector database.
        
        Args:
            content: The text content to add
            metadata: Additional information about the content
            
        Returns:
            The index of the added item
        """
        # Create embedding
        embedding = self._create_embedding(content)
        
        # Add embedding to FAISS index
        faiss.normalize_L2(np.array([embedding], dtype=np.float32))
        self.index.add(np.array([embedding], dtype=np.float32))
        
        # Add metadata with timestamp
        item_metadata = {
            **metadata,
            "content": content,
            "added_at": datetime.now().isoformat(),
            "id": len(self.metadata)
        }
        self.metadata.append(item_metadata)
        
        # Save the database
        self.save_db()
        
        return len(self.metadata) - 1
    
    def add_batch(self, items: List[Dict[str, Any]]) -> List[int]:
        """Add multiple items to the vector database in a batch.
        
        Args:
            items: List of dicts containing 'content' and 'metadata'
            
        Returns:
            List of indices for the added items
        """
        if not items:
            return []
        
        # Extract content and create embeddings
        contents = [item["content"] for item in items]
        embeddings = self.embedding_model.encode(contents)
        
        # Convert to float32 and normalize
        embeddings = np.array(embeddings, dtype=np.float32)
        faiss.normalize_L2(embeddings)
        
        # Add embeddings to FAISS index
        start_idx = len(self.metadata)
        self.index.add(embeddings)
        
        # Add metadata with timestamps
        for i, item in enumerate(items):
            item_metadata = {
                **item["metadata"],
                "content": item["content"],
                "added_at": datetime.now().isoformat(),
                "id": start_idx + i
            }
            self.metadata.append(item_metadata)
        
        # Save the database
        self.save_db()
        
        return list(range(start_idx, start_idx + len(items)))
    
    def search(self, query: str, k: int = 5) -> List[Dict[str, Any]]:
        """Search for similar content in the vector database.
        
        Args:
            query: The query text
            k: Number of results to return
            
        Returns:
            List of metadata for the most similar items
        """
        if len(self.metadata) == 0:
            return []
        
        # Create query embedding
        query_embedding = self._create_embedding(query)
        query_embedding = np.array([query_embedding], dtype=np.float32)
        faiss.normalize_L2(query_embedding)
        
        # Search FAISS index
        distances, indices = self.index.search(query_embedding, min(k, len(self.metadata)))
        
        # Return metadata for the results
        results = []
        for i, idx in enumerate(indices[0]):
            if idx >= 0 and idx < len(self.metadata):
                result = {**self.metadata[idx], "distance": float(distances[0][i])}
                results.append(result)
        
        return results
    
    def save_db(self) -> bool:
        """Save the vector database to disk.
        
        Returns:
            True if successful, False otherwise
        """
        try:
            # Create directory if it doesn't exist
            os.makedirs(VECTOR_DB_DIR, exist_ok=True)
            
            # Save FAISS index
            faiss.write_index(self.index, VECTOR_DB_PATH)
            
            # Save metadata
            with open(METADATA_PATH, 'wb') as f:
                pickle.dump(self.metadata, f)
            
            print(f"Vector database saved with {len(self.metadata)} entries")
            return True
        except Exception as e:
            print(f"Error saving vector database: {str(e)}")
            return False
    
    def load_db(self) -> bool:
        """Load the vector database from disk.
        
        Returns:
            True if successful, False otherwise
        """
        if not (os.path.exists(VECTOR_DB_PATH) and os.path.exists(METADATA_PATH)):
            print("No existing vector database found, starting fresh")
            return False
        
        try:
            # Load FAISS index
            self.index = faiss.read_index(VECTOR_DB_PATH)
            
            # Load metadata
            with open(METADATA_PATH, 'rb') as f:
                self.metadata = pickle.load(f)
            
            print(f"Loaded vector database with {len(self.metadata)} entries")
            return True
        except Exception as e:
            print(f"Error loading vector database: {str(e)}")
            # Reset to empty database
            self.index = faiss.IndexFlatL2(self.dimension)
            self.metadata = []
            return False
    
    def get_stats(self) -> Dict[str, Any]:
        """Get statistics about the vector database.
        
        Returns:
            Dictionary of statistics
        """
        return {
            "total_entries": len(self.metadata),
            "embedding_model": self.embedding_model_name,
            "embedding_dimension": self.dimension,
            "categories": self._count_categories()
        }
    
    def _count_categories(self) -> Dict[str, int]:
        """Count entries by category.
        
        Returns:
            Dictionary mapping categories to counts
        """
        category_counts = {}
        for item in self.metadata:
            category = item.get("category", "unknown")
            category_counts[category] = category_counts.get(category, 0) + 1
        return category_counts
    
    def clear(self) -> bool:
        """Clear the vector database.
        
        Returns:
            True if successful, False otherwise
        """
        try:
            # Reset to empty database
            self.index = faiss.IndexFlatL2(self.dimension)
            self.metadata = []
            self.save_db()
            print("Vector database cleared")
            return True
        except Exception as e:
            print(f"Error clearing vector database: {str(e)}")
            return False

# Singleton instance
_vectordb = None

def get_vectordb() -> FitnessVectorDB:
    """Get or create the singleton vector database instance.
    
    Returns:
        FitnessVectorDB instance
    """
    global _vectordb
    if _vectordb is None:
        _vectordb = FitnessVectorDB()
    return _vectordb 