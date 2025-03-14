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

async def analyze_with_openai_cached(
    messages: List[Dict[str, str]], 
    client_id: str = None, 
    query_key: str = None, 
    force_refresh: bool = False,
    temperature: float = 0.1,
    max_tokens: int = 500
) -> Dict[str, Any]:
    """
    Analyze data using OpenAI with caching.
    
    Args:
        messages: List of message dictionaries for the OpenAI API
        client_id: Optional client ID for cache key
        query_key: Optional query key for cache key
        force_refresh: Whether to force a refresh (ignore cache)
        temperature: Temperature for the OpenAI API call
        max_tokens: Maximum tokens for the response
        
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
    
    # Try to get from cache
    cached_response = None
    if openai_cache.enabled and not force_refresh:
        cache_key = f"{client_id}:{query_key}" if client_id and query_key else None
        cached_response = openai_cache.get(messages, model, custom_key=cache_key)
    
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
            temperature=temperature,
            max_tokens=max_tokens,
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
            cache_key = f"{client_id}:{query_key}" if client_id and query_key else None
            openai_cache.set(messages, model, cacheable_response, custom_key=cache_key)
        
        return result
    except Exception as e:
        print(f"Error calling OpenAI: {str(e)}")
        return {"content": f"Error during analysis: {str(e)}", "from_cache": False} 