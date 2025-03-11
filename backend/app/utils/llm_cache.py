"""
LLM Cache Module

This module provides caching functionality for LLM responses to reduce API costs and improve performance.
It implements:
1. Redis-based caching for LLM responses
2. TTL (time-to-live) for cache entries
3. Configurable cache settings

Environment variables:
- REDIS_URL: Redis connection string (optional, defaults to localhost)
- LLM_CACHE_TTL: Time-to-live for cache entries in seconds (optional, defaults to 1 day)
- LLM_CACHE_ENABLED: Whether caching is enabled (optional, defaults to True)
"""
import os
import json
import hashlib
from typing import Dict, Any, Optional, List
import redis
from datetime import timedelta
import logging

# Setup logging
logger = logging.getLogger(__name__)

class LLMCache:
    """Cache for LLM responses using Redis"""
    
    def __init__(self):
        self.enabled = os.getenv("LLM_CACHE_ENABLED", "true").lower() == "true"
        self.ttl = int(os.getenv("LLM_CACHE_TTL", 86400))  # Default: 1 day
        self.redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
        self.redis_client = None
        
        if self.enabled:
            try:
                self.redis_client = redis.from_url(self.redis_url)
                logger.info(f"LLM cache initialized with TTL: {self.ttl} seconds")
            except Exception as e:
                logger.error(f"Failed to connect to Redis: {str(e)}")
                logger.warning("LLM caching disabled due to Redis connection failure")
                self.enabled = False
    
    def _generate_cache_key(self, model: str, messages: List[Dict[str, str]], temperature: float) -> str:
        """Generate a unique cache key based on the request parameters"""
        # Convert messages to a stable string representation
        messages_str = json.dumps(messages, sort_keys=True)
        
        # Create a hash of the model, messages, and temperature
        key_string = f"{model}:{messages_str}:{temperature}"
        return hashlib.md5(key_string.encode()).hexdigest()
    
    def get(self, model: str, messages: List[Dict[str, str]], temperature: float) -> Optional[Dict[str, Any]]:
        """Get a cached response if available"""
        if not self.enabled or not self.redis_client:
            return None
        
        try:
            cache_key = self._generate_cache_key(model, messages, temperature)
            cached_data = self.redis_client.get(cache_key)
            
            if cached_data:
                logger.info(f"Cache hit for model {model}")
                return json.loads(cached_data)
            
            logger.info(f"Cache miss for model {model}")
            return None
        except Exception as e:
            logger.error(f"Error retrieving from cache: {str(e)}")
            return None
    
    def set(self, model: str, messages: List[Dict[str, str]], temperature: float, response: Dict[str, Any]) -> bool:
        """Store a response in the cache"""
        if not self.enabled or not self.redis_client:
            return False
        
        try:
            cache_key = self._generate_cache_key(model, messages, temperature)
            serialized_response = json.dumps(response)
            
            self.redis_client.setex(
                name=cache_key,
                time=timedelta(seconds=self.ttl),
                value=serialized_response
            )
            
            logger.info(f"Cached response for model {model}")
            return True
        except Exception as e:
            logger.error(f"Error storing in cache: {str(e)}")
            return False
    
    def invalidate(self, model: str, messages: List[Dict[str, str]], temperature: float) -> bool:
        """Invalidate a specific cache entry"""
        if not self.enabled or not self.redis_client:
            return False
        
        try:
            cache_key = self._generate_cache_key(model, messages, temperature)
            result = self.redis_client.delete(cache_key)
            
            if result:
                logger.info(f"Invalidated cache for model {model}")
                return True
            
            logger.info(f"No cache entry found to invalidate for model {model}")
            return False
        except Exception as e:
            logger.error(f"Error invalidating cache: {str(e)}")
            return False
    
    def flush(self) -> bool:
        """Flush all cache entries (use with caution)"""
        if not self.enabled or not self.redis_client:
            return False
        
        try:
            # Use a pattern to only clear LLM cache keys
            # This assumes we're using a dedicated Redis database or have a prefix system
            self.redis_client.flushdb()
            logger.info("Flushed all cache entries")
            return True
        except Exception as e:
            logger.error(f"Error flushing cache: {str(e)}")
            return False

# Create a singleton instance
llm_cache = LLMCache()