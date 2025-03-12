"""
OpenAI Analysis Module

This module provides cached analysis functions using OpenAI.
It works with the OpenAI cache module to provide cached results.
"""

import json
import hashlib
import os
from typing import Dict, Any, List
from datetime import datetime
from openai import AsyncOpenAI
from .openai_cache import openai_cache

async def analyze_with_openai_cached(client_name: str, workout_data: List[Dict], query: str, rag_context: str = "") -> Dict[str, Any]:
    """
    Analyze client workout data using OpenAI with caching.
    
    Args:
        client_name: The name of the client
        workout_data: List of workout dictionaries
        query: The analysis query
        rag_context: Optional RAG context to include
        
    Returns:
        Dictionary with analysis result
    """
    # Get API key
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("WARNING: No OpenAI API key found. Using dummy response.")
        return {"content": "API key not configured. This is a placeholder response.", "from_cache": False}
    
    # Initialize OpenAI client
    client = AsyncOpenAI(api_key=api_key)
    
    # Get the preferred model
    model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
    
    # Prepare the messages
    messages = [
        {"role": "system", "content": "You are a fitness analysis assistant that helps trainers understand their clients' workout data. Provide concise, actionable insights."},
        {"role": "system", "content": f"Here is some relevant fitness knowledge to help you provide accurate information:\n\n{rag_context}"},
        {"role": "user", "content": f"Analyze the following workout data for client {client_name}. Question: {query}"},
        {"role": "system", "content": f"Here's the workout data: {json.dumps(workout_data)}"}
    ]
    
    # Try to get from cache
    cached_response = None
    if openai_cache.enabled:
        cached_response = openai_cache.get(messages, model)
    
    if cached_response:
        # Format the cached response
        return {
            "content": cached_response["choices"][0]["message"]["content"],
            "from_cache": True
        }
    
    # Call OpenAI API
    try:
        response = await client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=0.1,
            max_tokens=500,
        )
        
        # Get the result
        result = {
            "content": response.choices[0].message.content,
            "from_cache": False
        }
        
        # Cache the result
        if openai_cache.enabled:
            cacheable_response = {
                "model": model,
                "choices": [
                    {
                        "message": {
                            "content": result["content"],
                            "role": "assistant"
                        },
                        "index": 0
                    }
                ],
                "created": int(datetime.now().timestamp()),
                "cached": True
            }
            openai_cache.set(messages, model, cacheable_response)
        
        return result
    except Exception as e:
        print(f"Error calling OpenAI: {str(e)}")
        return {"content": f"Error during analysis: {str(e)}", "from_cache": False} 