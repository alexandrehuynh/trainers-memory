"""
Fitness Domain Embedding Tools

This module provides tools for creating and managing fitness domain embeddings
for use in the vector database and RAG system.
"""

import os
from typing import Dict, List, Any, Optional
import numpy as np
import torch
from sentence_transformers import SentenceTransformer, InputExample, losses
from torch.utils.data import DataLoader
from ..vectordb import get_vectordb
from .knowledge_base import load_fitness_knowledge

def create_fitness_embeddings(force_refresh: bool = False) -> Dict[str, int]:
    """Create embeddings for fitness domain knowledge and add to vector database.
    
    Args:
        force_refresh: If True, clear existing embeddings before adding new ones
        
    Returns:
        Dictionary with counts of embeddings created by category
    """
    # Get vector database
    vectordb = get_vectordb()
    
    # Clear existing embeddings if requested
    if force_refresh:
        vectordb.clear()
    
    # Skip if database already has entries and not forcing refresh
    if len(vectordb.metadata) > 0 and not force_refresh:
        print(f"Vector database already contains {len(vectordb.metadata)} entries. Use force_refresh=True to recreate.")
        return vectordb.get_stats()["categories"]
    
    # Load fitness knowledge
    knowledge = load_fitness_knowledge()
    
    # Track counts
    counts = {"exercises": 0, "principles": 0, "terminology": 0, "safety": 0}
    
    # Process exercises
    exercise_items = []
    for exercise in knowledge["exercises"]:
        # Create main exercise entry
        content = f"Exercise: {exercise['name']}\n\nDescription: {exercise['description']}\n\nMuscles: {', '.join(exercise['primary_muscles'])}\n\nDifficulty: {exercise['difficulty']}"
        
        # Add technique tips if available
        if exercise.get("technique_tips"):
            content += f"\n\nTechnique Tips:\n" + "\n".join([f"- {tip}" for tip in exercise["technique_tips"]])
        
        # Create item for batch processing
        exercise_items.append({
            "content": content,
            "metadata": {
                "type": "exercise",
                "name": exercise["name"],
                "category": exercise.get("category", "Unknown"),
                "muscles": exercise.get("primary_muscles", []),
                "difficulty": exercise.get("difficulty", "Intermediate"),
                "equipment": exercise.get("equipment", [])
            }
        })
        
        # Create entries for variations if available
        if exercise.get("variations"):
            for variation in exercise["variations"]:
                variation_content = f"Exercise Variation: {variation}\n\nThis is a variation of {exercise['name']}.\n\n{exercise['description']}"
                exercise_items.append({
                    "content": variation_content,
                    "metadata": {
                        "type": "exercise_variation",
                        "name": variation,
                        "parent_exercise": exercise["name"],
                        "category": exercise.get("category", "Unknown"),
                        "muscles": exercise.get("primary_muscles", [])
                    }
                })
    
    # Add exercises in batch
    if exercise_items:
        indices = vectordb.add_batch(exercise_items)
        counts["exercises"] = len(indices)
        print(f"Added {len(indices)} exercise embeddings to vector database")
    
    # Process training principles
    principle_items = []
    for principle in knowledge["principles"]:
        content = f"Training Principle: {principle['name']}\n\nDescription: {principle['description']}"
        
        # Add application if available
        if principle.get("application"):
            content += f"\n\nApplication:\n" + "\n".join([f"- {app}" for app in principle["application"]])
        
        # Add importance if available
        if principle.get("importance"):
            content += f"\n\nImportance: {principle['importance']}"
        
        principle_items.append({
            "content": content,
            "metadata": {
                "type": "principle",
                "name": principle["name"],
                "category": principle.get("category", "Training Principle")
            }
        })
    
    # Add principles in batch
    if principle_items:
        indices = vectordb.add_batch(principle_items)
        counts["principles"] = len(indices)
        print(f"Added {len(indices)} principle embeddings to vector database")
    
    # Process terminology
    terminology_items = []
    for term in knowledge["terminology"]:
        content = f"Fitness Term: {term['term']}\n\nDefinition: {term['definition']}"
        
        # Add example if available
        if term.get("example"):
            content += f"\n\nExample: {term['example']}"
        
        terminology_items.append({
            "content": content,
            "metadata": {
                "type": "terminology",
                "term": term["term"],
                "category": term.get("category", "Terminology")
            }
        })
    
    # Add terminology in batch
    if terminology_items:
        indices = vectordb.add_batch(terminology_items)
        counts["terminology"] = len(indices)
        print(f"Added {len(indices)} terminology embeddings to vector database")
    
    # Process safety guidelines
    safety_items = []
    for guideline in knowledge["safety"]:
        content = f"Safety Guideline: {guideline['title']}\n\nDescription: {guideline['description']}"
        
        # Add specific guidelines if available
        if guideline.get("guidelines"):
            content += f"\n\nGuidelines:\n" + "\n".join([f"- {g}" for g in guideline["guidelines"]])
        
        # Add importance if available
        if guideline.get("importance"):
            content += f"\n\nImportance: {guideline['importance']}"
        
        safety_items.append({
            "content": content,
            "metadata": {
                "type": "safety",
                "title": guideline["title"],
                "category": guideline.get("category", "Safety")
            }
        })
    
    # Add safety guidelines in batch
    if safety_items:
        indices = vectordb.add_batch(safety_items)
        counts["safety"] = len(indices)
        print(f"Added {len(indices)} safety guideline embeddings to vector database")
    
    # Return counts
    return counts

def search_fitness_knowledge(query: str, k: int = 5) -> List[Dict[str, Any]]:
    """Search for fitness knowledge using the vector database.
    
    Args:
        query: The search query
        k: Number of results to return
        
    Returns:
        List of search results with metadata
    """
    # Get vector database
    vectordb = get_vectordb()
    
    # Create embeddings if database is empty
    if len(vectordb.metadata) == 0:
        print("Vector database is empty. Creating fitness embeddings...")
        create_fitness_embeddings()
    
    # Search for similar content
    results = vectordb.search(query, k=k)
    
    return results

def get_rag_context(query: str, max_tokens: int = 1000) -> str:
    """Get RAG context for a query by searching the fitness knowledge base.
    
    Args:
        query: The user query
        max_tokens: Maximum tokens to include in context
        
    Returns:
        String containing relevant context for the query
    """
    # Search for relevant knowledge
    results = search_fitness_knowledge(query, k=5)
    
    if not results:
        return "No relevant fitness knowledge found."
    
    # Build context string
    context = "Relevant fitness knowledge:\n\n"
    
    for i, result in enumerate(results):
        # Add content with separator
        context += f"--- Knowledge Item {i+1} ---\n"
        context += result["content"]
        context += "\n\n"
    
    # Truncate if too long (rough approximation)
    if len(context) > max_tokens * 4:  # Assuming ~4 chars per token
        context = context[:max_tokens * 4] + "...[truncated]"
    
    return context

def train_fitness_domain_embedding(output_model_name: str = "fitness-domain-v1", 
                                  base_model: str = "all-MiniLM-L6-v2",
                                  epochs: int = 10,
                                  batch_size: int = 16,
                                  learning_rate: float = 2e-5) -> str:
    """
    Fine-tune a sentence transformer model on fitness domain data to create
    specialized fitness embeddings.
    
    Args:
        output_model_name: Name for the saved model
        base_model: Base model to fine-tune
        epochs: Number of training epochs
        batch_size: Training batch size
        learning_rate: Learning rate for training
        
    Returns:
        Path to the saved model
    """
    # Load fitness knowledge
    knowledge = load_fitness_knowledge()
    
    # Create training data from exercises
    training_examples = []
    
    # Exercise pairs (similar exercises should have similar embeddings)
    for i, exercise1 in enumerate(knowledge["exercises"]):
        # Create positive pairs (same muscle groups)
        for j, exercise2 in enumerate(knowledge["exercises"]):
            if i != j:
                # Check if they share primary muscles
                common_muscles = set(exercise1["primary_muscles"]).intersection(set(exercise2["primary_muscles"]))
                if common_muscles:
                    similarity = len(common_muscles) / max(len(exercise1["primary_muscles"]), len(exercise2["primary_muscles"]))
                    if similarity > 0.5:  # Only use exercises with significant muscle overlap
                        # Create a training example with the exercise descriptions
                        training_examples.append(InputExample(
                            texts=[
                                f"Exercise: {exercise1['name']}. {exercise1['description']}",
                                f"Exercise: {exercise2['name']}. {exercise2['description']}"
                            ],
                            label=similarity  # Use muscle overlap as a similarity score
                        ))
    
    # Add terminology pairs
    for i, term1 in enumerate(knowledge["terminology"]):
        for j, term2 in enumerate(knowledge["terminology"]):
            if i != j and term1["category"] == term2["category"]:
                # Terms in the same category should be somewhat similar
                training_examples.append(InputExample(
                    texts=[
                        f"{term1['term']}: {term1['definition']}",
                        f"{term2['term']}: {term2['definition']}"
                    ],
                    label=0.7  # Terms in the same category are fairly similar
                ))
    
    # Add training principles
    for i, principle1 in enumerate(knowledge["principles"]):
        for j, principle2 in enumerate(knowledge["principles"]):
            if i != j:
                # All training principles should have some relationship
                training_examples.append(InputExample(
                    texts=[
                        f"{principle1['name']}: {principle1['description']}",
                        f"{principle2['name']}: {principle2['description']}"
                    ],
                    label=0.5  # Moderate similarity for principles
                ))
    
    # Load base model
    model = SentenceTransformer(base_model)
    
    # Create data loader
    train_dataloader = DataLoader(training_examples, shuffle=True, batch_size=batch_size)
    
    # Use cosine similarity loss
    train_loss = losses.CosineSimilarityLoss(model)
    
    # Train the model
    print(f"Training fitness domain embedding model with {len(training_examples)} examples for {epochs} epochs")
    model.fit(
        train_objectives=[(train_dataloader, train_loss)],
        epochs=epochs,
        warmup_steps=int(len(train_dataloader) * 0.1),
        optimizer_params={'lr': learning_rate},
        show_progress_bar=True
    )
    
    # Save the model
    output_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "models", output_model_name)
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    model.save(output_path)
    
    print(f"Fitness domain embedding model saved to {output_path}")
    
    # Update the vector database to use the new model
    vectordb = get_vectordb(embedding_model=output_path)
    
    # Recreate embeddings with the new model
    create_fitness_embeddings(force_refresh=True)
    
    return output_path 