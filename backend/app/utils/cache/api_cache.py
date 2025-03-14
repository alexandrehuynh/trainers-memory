"""
API Response Caching Module

This module provides caching functionality for third-party API responses to:
1. Reduce API costs by minimizing redundant calls
2. Improve response times for frequently requested data
3. Handle rate limits gracefully by serving cached data when limits are reached

The caching is implemented with both an in-memory cache (for fast access) and
Redis cache (for persistence and sharing across instances).
"""

import json
import logging
import functools
import time
import hashlib
from typing import Any, Callable, Dict, Optional, TypeVar, Awaitable
import redis
import os
from datetime import datetime, timedelta
import asyncio

# Configure logging
logger = logging.getLogger(__name__)

# Type variable for better type hints with decorators
T = TypeVar('T')

# Initialize Redis connection if available
REDIS_URL = os.environ.get("REDIS_URL", "redis://localhost:6379/0")
REDIS_ENABLED = os.environ.get("REDIS_ENABLED", "true").lower() == "true"

try:
    if REDIS_ENABLED:
        redis_client = redis.from_url(REDIS_URL)
        redis_client.ping()  # Test connection
        logger.info("Redis connection established for API caching")
    else:
        redis_client = None
        logger.info("Redis caching disabled through environment variable")
except Exception as e:
    redis_client = None
    logger.warning(f"Failed to connect to Redis, using in-memory cache only: {str(e)}")

# In-memory cache as fallback
in_memory_cache = {}

def get_cache_key(prefix: str, *args, **kwargs) -> str:
    """
    Generate a unique cache key based on function arguments.
    
    Args:
        prefix: A prefix for the cache key (usually function name)
        *args: Positional arguments to include in key generation
        **kwargs: Keyword arguments to include in key generation
        
    Returns:
        A unique string key for caching
    """
    # Convert args and kwargs to a string representation
    key_dict = {
        "args": args,
        "kwargs": {k: v for k, v in kwargs.items() if k != "force_refresh"}
    }
    
    # Hash the JSON representation
    key_str = json.dumps(key_dict, sort_keys=True)
    key_hash = hashlib.md5(key_str.encode()).hexdigest()
    
    return f"{prefix}:{key_hash}"

async def get_cached_data(cache_key: str, ttl: int = 3600) -> Optional[Any]:
    """
    Retrieve data from cache (Redis if available, otherwise in-memory).
    
    Args:
        cache_key: The unique key to look up
        ttl: Time-to-live in seconds (used for checking in-memory cache expiry)
        
    Returns:
        Cached data if found and not expired, None otherwise
    """
    # Try Redis first if available
    if redis_client:
        try:
            cached_data = redis_client.get(cache_key)
            if cached_data:
                return json.loads(cached_data)
        except Exception as e:
            logger.warning(f"Redis get error, falling back to in-memory cache: {str(e)}")
    
    # Fall back to in-memory cache
    if cache_key in in_memory_cache:
        cached_item = in_memory_cache[cache_key]
        # Check if the in-memory cache has expired
        if cached_item["expires_at"] > time.time():
            return cached_item["data"]
        else:
            # Clean up expired item
            del in_memory_cache[cache_key]
    
    return None

async def set_cached_data(cache_key: str, data: Any, ttl: int = 3600) -> None:
    """
    Store data in cache (Redis if available, and in-memory).
    
    Args:
        cache_key: The unique key to store the data under
        data: The data to cache (must be JSON serializable)
        ttl: Time-to-live in seconds
    """
    # Try to cache in Redis if available
    if redis_client:
        try:
            redis_client.setex(
                cache_key,
                ttl,
                json.dumps(data)
            )
        except Exception as e:
            logger.warning(f"Redis set error, using in-memory cache only: {str(e)}")
    
    # Always cache in memory too for faster access
    in_memory_cache[cache_key] = {
        "data": data,
        "expires_at": time.time() + ttl
    }

def async_cache_response(ttl: int = 3600):
    """
    Decorator for caching async function responses.
    
    Args:
        ttl: Time-to-live in seconds for the cached data
        
    Returns:
        Decorator function
    """
    def decorator(func: Callable[..., Awaitable[T]]) -> Callable[..., Awaitable[T]]:
        @functools.wraps(func)
        async def wrapper(*args, **kwargs) -> T:
            # Check if caching should be bypassed
            force_refresh = kwargs.pop("force_refresh", False)
            
            # Generate a unique cache key
            cache_key = get_cache_key(func.__name__, *args, **kwargs)
            
            # Try to get cached response if not forcing refresh
            if not force_refresh:
                cached_data = await get_cached_data(cache_key, ttl)
                if cached_data is not None:
                    logger.debug(f"Cache hit for {func.__name__}")
                    return cached_data
            
            # Cache miss or force refresh, call the original function
            logger.debug(f"Cache miss for {func.__name__}, fetching fresh data")
            result = await func(*args, **kwargs)
            
            # Cache the result
            await set_cached_data(cache_key, result, ttl)
            
            return result
        return wrapper
    return decorator

def clear_cache_by_prefix(prefix: str) -> int:
    """
    Clear all cache entries that start with the given prefix.
    
    Args:
        prefix: The prefix to match against cache keys
        
    Returns:
        Number of cache entries cleared
    """
    count = 0
    
    # Clear from Redis if available
    if redis_client:
        try:
            # Find keys matching the pattern
            matching_keys = redis_client.keys(f"{prefix}:*")
            if matching_keys:
                # Delete all matching keys
                count += redis_client.delete(*matching_keys)
        except Exception as e:
            logger.warning(f"Redis deletion error: {str(e)}")
    
    # Clear from in-memory cache
    memory_keys_to_delete = [k for k in in_memory_cache.keys() if k.startswith(f"{prefix}:")]
    for k in memory_keys_to_delete:
        del in_memory_cache[k]
        count += 1
    
    return count 