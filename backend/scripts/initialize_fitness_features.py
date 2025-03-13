#!/usr/bin/env python3
"""
Initialize Fitness Features Script

This script initializes the fitness features developed for weeks 3-4:
1. RAG (Retrieval Augmented Generation) for fitness knowledge enhancement
2. Fitness domain embeddings trained on exercise terminology
3. Synthetic training data for fitness-specific scenarios

Run this script after setting up the backend to prepare all fitness-related
features for use in the API.
"""

import os
import sys
import argparse
import json
from pathlib import Path

# Add the backend directory to the path so we can import from app
sys.path.append(str(Path(__file__).parent.parent))

from app.utils.fitness_data.embedding_tools import create_fitness_embeddings, train_fitness_domain_embedding
from app.utils.fitness_data.knowledge_base import (
    generate_synthetic_training_data, 
    save_synthetic_data,
    load_fitness_knowledge
)
from app.utils.vectordb import get_vectordb

def initialize_rag():
    """Initialize the RAG system by creating embeddings for fitness knowledge."""
    print("\n=== Initializing RAG (Retrieval Augmented Generation) ===")
    
    # Create embeddings for fitness knowledge
    result = create_fitness_embeddings(force_refresh=True)
    
    # Print statistics
    print(f"Created embeddings for fitness knowledge:")
    for category, count in result.items():
        print(f"  - {category}: {count} items")
    
    # Test the RAG system
    vectordb = get_vectordb()
    print(f"\nVector database stats: {vectordb.get_stats()}")
    
    # Test a sample query
    test_query = "What's the best way to train for hypertrophy?"
    results = vectordb.search(test_query, k=3)
    
    print(f"\nTest query: '{test_query}'")
    print(f"Top 3 retrieval results:")
    for i, result in enumerate(results):
        print(f"  {i+1}. {result['metadata'].get('name', result['metadata'].get('title', 'Unknown'))} "
              f"({result['metadata']['category']}) - Score: {result['score']:.3f}")
    
    print("\nRAG system initialized successfully!")
    return True

def train_fitness_embeddings(epochs=5):
    """Train domain-specific embeddings for fitness terminology."""
    print("\n=== Training Fitness Domain Embeddings ===")
    
    # Train the model
    model_path = train_fitness_domain_embedding(
        output_model_name="fitness-domain-v1",
        base_model="all-MiniLM-L6-v2",
        epochs=epochs,
        batch_size=16,
        learning_rate=2e-5
    )
    
    print(f"\nFitness domain embedding model saved to: {model_path}")
    print("Fitness domain embeddings trained successfully!")
    return model_path

def generate_training_data(num_clients=20, workouts_per_client=10):
    """Generate synthetic training data for fitness scenarios."""
    print(f"\n=== Generating Synthetic Training Data ===")
    print(f"Generating data for {num_clients} clients with {workouts_per_client} workouts each...")
    
    # Generate the data
    data = generate_synthetic_training_data(
        num_clients=num_clients,
        workouts_per_client=workouts_per_client
    )
    
    # Save the data
    data_dir = Path(__file__).parent.parent / "data" / "synthetic"
    data_dir.mkdir(parents=True, exist_ok=True)
    output_file = data_dir / "fitness_synthetic_data.json"
    
    save_synthetic_data(data, str(output_file))
    
    print(f"Generated {len(data['clients'])} synthetic client profiles")
    print(f"Generated {len(data['workouts'])} synthetic workouts")
    print(f"Saved synthetic data to: {output_file}")
    print("Synthetic training data generated successfully!")
    return str(output_file)

def main():
    """Main function to initialize all fitness features."""
    parser = argparse.ArgumentParser(description="Initialize fitness features for the Trainer's Memory API")
    parser.add_argument("--skip-rag", action="store_true", help="Skip RAG initialization")
    parser.add_argument("--skip-embeddings", action="store_true", help="Skip fitness domain embeddings training")
    parser.add_argument("--skip-synthetic-data", action="store_true", help="Skip synthetic data generation")
    parser.add_argument("--clients", type=int, default=20, help="Number of synthetic clients to generate")
    parser.add_argument("--workouts", type=int, default=10, help="Number of workouts per client")
    parser.add_argument("--epochs", type=int, default=5, help="Number of epochs for embedding training")
    
    args = parser.parse_args()
    
    print("=== Initializing Fitness Features for Trainer's Memory API ===")
    
    results = {}
    
    # Initialize RAG
    if not args.skip_rag:
        results["rag_success"] = initialize_rag()
    else:
        print("\nSkipping RAG initialization.")
    
    # Train fitness domain embeddings
    if not args.skip_embeddings:
        results["embedding_model_path"] = train_fitness_embeddings(epochs=args.epochs)
    else:
        print("\nSkipping fitness domain embeddings training.")
    
    # Generate synthetic training data
    if not args.skip_synthetic_data:
        results["synthetic_data_path"] = generate_training_data(
            num_clients=args.clients,
            workouts_per_client=args.workouts
        )
    else:
        print("\nSkipping synthetic data generation.")
    
    print("\n=== Fitness Features Initialization Complete! ===")
    print("Summary:")
    if "rag_success" in results:
        print("- RAG System: Initialized successfully")
    if "embedding_model_path" in results:
        print(f"- Fitness Domain Embeddings: Trained and saved to {results['embedding_model_path']}")
    if "synthetic_data_path" in results:
        print(f"- Synthetic Training Data: Generated and saved to {results['synthetic_data_path']}")
    
    return results

if __name__ == "__main__":
    main() 