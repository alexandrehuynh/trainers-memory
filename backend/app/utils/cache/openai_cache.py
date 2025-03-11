"""
OpenAI Cache Module

This module provides Redis-based caching for OpenAI responses to:
1. Reduce API costs by reusing identical queries
2. Improve response time for common queries
3. Maintain availability during rate limiting

The cache stores responses with configurable TTL (time-to-live) and
supports cache invalidation based on parameters like client_id.
"""

import json
import hashlib
import os
from typing import Optional, Dict, Any, List
import redis
from datetime import datetime, timedelta

class OpenAICache:
    """Redis-based cache for OpenAI responses."""
    
    def __init__(self):
        """Initialize the cache with Redis connection."""
        redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
        self.redis = redis.Redis.from_url(redis_url, decode_responses=True)
        
        # Default TTL (time-to-live) for cache entries (1 hour)
        self.default_ttl = int(os.getenv("OPENAI_CACHE_TTL", 3600))
        
        # Cache prefix to avoid collisions with other data
        self.prefix = "openai_cache:"
        
        # Testing if Redis is available
        try:
            self.redis.ping()
            self.enabled = True
            print("✓ Redis cache for OpenAI is enabled and connected")
        except redis.exceptions.ConnectionError:
            self.enabled = False
            print("✗ Redis cache for OpenAI failed to connect - caching disabled")
    
    def _generate_key(self, messages: List[Dict[str, str]], model: str) -> str:
        """Generate a cache key based on messages and model.
        
        Args:
            messages: List of message dictionaries to send to OpenAI
            model: The OpenAI model being used
            
        Returns:
            A string hash key for the cache
        """
        # Create a deterministic representation of the messages
        content_str = json.dumps(messages, sort_keys=True)
        
        # Create a hash of the content and model
        key_components = f"{content_str}:{model}"
        cache_key = hashlib.md5(key_components.encode('utf-8')).hexdigest()
        
        # Return the prefixed key
        return f"{self.prefix}{cache_key}"
    
    def get(self, messages: List[Dict[str, str]], model: str) -> Optional[Dict[str, Any]]:
        """Retrieve a cached response if available.
        
        Args:
            messages: List of message dictionaries to send to OpenAI
            model: The OpenAI model being used
            
        Returns:
            The cached response or None if not found
        """
        if not self.enabled:
            return None
            
        key = self._generate_key(messages, model)
        
        try:
            cached_data = self.redis.get(key)
            if cached_data:
                print(f"Cache hit for OpenAI query with model {model}")
                return json.loads(cached_data)
        except Exception as e:
            print(f"Error retrieving from cache: {str(e)}")
        
        return None
    
    def set(self, messages: List[Dict[str, str]], model: str, response: Dict[str, Any], ttl: Optional[int] = None) -> bool:
        """Store a response in the cache.
        
        Args:
            messages: List of message dictionaries sent to OpenAI
            model: The OpenAI model used
            response: The response to cache
            ttl: Optional time-to-live in seconds (default: 1 hour)
            
        Returns:
            True if successful, False otherwise
        """
        if not self.enabled:
            return False
            
        key = self._generate_key(messages, model)
        ttl = ttl if ttl is not None else self.default_ttl
        
        try:
            # Store with expiration time
            serialized = json.dumps(response)
            success = self.redis.setex(key, ttl, serialized)
            if success:
                print(f"Cached OpenAI response for model {model} (TTL: {ttl}s)")
            return success
        except Exception as e:
            print(f"Error storing in cache: {str(e)}")
            return False
    
    def invalidate_by_client(self, client_id: str) -> int:
        """Invalidate all cache entries for a specific client.
        
        Args:
            client_id: The client ID to invalidate cache for
            
        Returns:
            Number of entries invalidated
        """
        if not self.enabled:
            return 0
            
        try:
            # We need to scan all keys and check if they contain the client_id
            # This is not ideal for performance but works for moderate size caches
            cursor = 0
            count = 0
            
            # Use scan to iterate through keys
            while True:
                cursor, keys = self.redis.scan(cursor, f"{self.prefix}*", 100)
                for key in keys:
                    cached_data = self.redis.get(key)
                    if cached_data and client_id in cached_data:
                        self.redis.delete(key)
                        count += 1
                
                # Break when no more keys
                if cursor == 0:
                    break
            
            if count > 0:
                print(f"Invalidated {count} cache entries for client {client_id}")
            return count
        except Exception as e:
            print(f"Error invalidating cache: {str(e)}")
            return 0
    
    def clear_all(self) -> int:
        """Clear all OpenAI cache entries.
        
        Returns:
            Number of entries cleared
        """
        if not self.enabled:
            return 0
            
        try:
            cursor = 0
            count = 0
            
            # Use scan to iterate through keys
            while True:
                cursor, keys = self.redis.scan(cursor, f"{self.prefix}*", 100)
                if keys:
                    count += len(keys)
                    self.redis.delete(*keys)
                
                # Break when no more keys
                if cursor == 0:
                    break
            
            if count > 0:
                print(f"Cleared {count} entries from OpenAI cache")
            return count
        except Exception as e:
            print(f"Error clearing cache: {str(e)}")
            return 0

# Create a singleton instance
openai_cache = OpenAICache() 