"""
Caching layer for HealthInsightCore
Provides in-memory caching for frequently accessed data
"""

import asyncio
import json
import time
from typing import Any, Dict, Optional, Union, List
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)


class CacheEntry:
    """Cache entry with expiration"""
    
    def __init__(self, value: Any, ttl_seconds: int = 300):
        self.value = value
        self.created_at = time.time()
        self.ttl_seconds = ttl_seconds
    
    def is_expired(self) -> bool:
        """Check if cache entry has expired"""
        return time.time() - self.created_at > self.ttl_seconds
    
    def get_age_seconds(self) -> float:
        """Get age of cache entry in seconds"""
        return time.time() - self.created_at


class InMemoryCache:
    """Simple in-memory cache with TTL support"""
    
    def __init__(self, default_ttl: int = 300, max_size: int = 1000):
        self.cache: Dict[str, CacheEntry] = {}
        self.default_ttl = default_ttl
        self.max_size = max_size
        self.hits = 0
        self.misses = 0
        self._lock = asyncio.Lock()
    
    async def get(self, key: str) -> Optional[Any]:
        """Get value from cache"""
        async with self._lock:
            entry = self.cache.get(key)
            
            if entry is None:
                self.misses += 1
                return None
            
            if entry.is_expired():
                del self.cache[key]
                self.misses += 1
                return None
            
            self.hits += 1
            return entry.value
    
    async def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """Set value in cache"""
        async with self._lock:
            # Evict expired entries if cache is full
            if len(self.cache) >= self.max_size:
                await self._evict_expired()
                
                # If still full, evict oldest entries
                if len(self.cache) >= self.max_size:
                    await self._evict_oldest(self.max_size // 4)  # Evict 25%
            
            ttl_seconds = ttl or self.default_ttl
            self.cache[key] = CacheEntry(value, ttl_seconds)
    
    async def delete(self, key: str) -> bool:
        """Delete key from cache"""
        async with self._lock:
            if key in self.cache:
                del self.cache[key]
                return True
            return False
    
    async def clear(self) -> None:
        """Clear all cache entries"""
        async with self._lock:
            self.cache.clear()
            self.hits = 0
            self.misses = 0
    
    async def _evict_expired(self) -> None:
        """Remove expired entries"""
        expired_keys = [
            key for key, entry in self.cache.items()
            if entry.is_expired()
        ]
        for key in expired_keys:
            del self.cache[key]
    
    async def _evict_oldest(self, count: int) -> None:
        """Remove oldest entries"""
        if count <= 0:
            return
        
        # Sort by creation time and remove oldest
        sorted_items = sorted(
            self.cache.items(),
            key=lambda x: x[1].created_at
        )
        
        for i in range(min(count, len(sorted_items))):
            key = sorted_items[i][0]
            del self.cache[key]
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        total_requests = self.hits + self.misses
        hit_rate = (self.hits / total_requests * 100) if total_requests > 0 else 0
        
        return {
            "size": len(self.cache),
            "max_size": self.max_size,
            "hits": self.hits,
            "misses": self.misses,
            "hit_rate_percent": round(hit_rate, 2),
            "total_requests": total_requests
        }


class CacheManager:
    """Cache manager with different cache instances for different data types"""
    
    def __init__(self):
        # Different caches for different data types with appropriate TTLs
        self.user_cache = InMemoryCache(default_ttl=600, max_size=500)  # 10 minutes
        self.report_cache = InMemoryCache(default_ttl=300, max_size=1000)  # 5 minutes
        self.analysis_cache = InMemoryCache(default_ttl=1800, max_size=500)  # 30 minutes
        self.search_cache = InMemoryCache(default_ttl=120, max_size=200)  # 2 minutes
        self.metrics_cache = InMemoryCache(default_ttl=300, max_size=300)  # 5 minutes
    
    # User cache methods
    async def get_user(self, uid: str) -> Optional[Dict[str, Any]]:
        """Get user from cache"""
        return await self.user_cache.get(f"user:{uid}")
    
    async def set_user(self, uid: str, user_data: Dict[str, Any]) -> None:
        """Set user in cache"""
        await self.user_cache.set(f"user:{uid}", user_data)
    
    async def invalidate_user(self, uid: str) -> None:
        """Invalidate user cache"""
        await self.user_cache.delete(f"user:{uid}")
    
    # Report cache methods
    async def get_report(self, report_id: str) -> Optional[Dict[str, Any]]:
        """Get report from cache"""
        return await self.report_cache.get(f"report:{report_id}")
    
    async def set_report(self, report_id: str, report_data: Dict[str, Any]) -> None:
        """Set report in cache"""
        await self.report_cache.set(f"report:{report_id}", report_data)
    
    async def invalidate_report(self, report_id: str) -> None:
        """Invalidate report cache"""
        await self.report_cache.delete(f"report:{report_id}")
    
    async def get_patient_reports(self, patient_id: str, skip: int = 0, limit: int = 50) -> Optional[List[Dict[str, Any]]]:
        """Get patient reports from cache"""
        cache_key = f"patient_reports:{patient_id}:{skip}:{limit}"
        return await self.report_cache.get(cache_key)
    
    async def set_patient_reports(self, patient_id: str, reports: List[Dict[str, Any]], skip: int = 0, limit: int = 50) -> None:
        """Set patient reports in cache"""
        cache_key = f"patient_reports:{patient_id}:{skip}:{limit}"
        await self.report_cache.set(cache_key, reports, ttl=180)  # Shorter TTL for lists
    
    async def invalidate_patient_reports(self, patient_id: str) -> None:
        """Invalidate all cached reports for a patient"""
        # This is a simple approach - in production, you might want pattern-based deletion
        keys_to_delete = [
            key for key in self.report_cache.cache.keys()
            if key.startswith(f"patient_reports:{patient_id}:")
        ]
        for key in keys_to_delete:
            await self.report_cache.delete(key)
    
    # Analysis cache methods
    async def get_analysis(self, report_id: str) -> Optional[Dict[str, Any]]:
        """Get analysis from cache"""
        return await self.analysis_cache.get(f"analysis:{report_id}")
    
    async def set_analysis(self, report_id: str, analysis_data: Dict[str, Any]) -> None:
        """Set analysis in cache"""
        await self.analysis_cache.set(f"analysis:{report_id}", analysis_data)
    
    async def get_trend_analysis(self, patient_id: str, metrics_hash: str) -> Optional[Dict[str, Any]]:
        """Get trend analysis from cache"""
        cache_key = f"trend:{patient_id}:{metrics_hash}"
        return await self.analysis_cache.get(cache_key)
    
    async def set_trend_analysis(self, patient_id: str, metrics_hash: str, trend_data: Dict[str, Any]) -> None:
        """Set trend analysis in cache"""
        cache_key = f"trend:{patient_id}:{metrics_hash}"
        await self.analysis_cache.set(cache_key, trend_data, ttl=900)  # 15 minutes
    
    # Search cache methods
    async def get_search_results(self, search_hash: str) -> Optional[Dict[str, Any]]:
        """Get search results from cache"""
        return await self.search_cache.get(f"search:{search_hash}")
    
    async def set_search_results(self, search_hash: str, results: Dict[str, Any]) -> None:
        """Set search results in cache"""
        await self.search_cache.set(f"search:{search_hash}", results)
    
    # Metrics cache methods
    async def get_dashboard_data(self, patient_id: str) -> Optional[Dict[str, Any]]:
        """Get dashboard data from cache"""
        return await self.metrics_cache.get(f"dashboard:{patient_id}")
    
    async def set_dashboard_data(self, patient_id: str, dashboard_data: Dict[str, Any]) -> None:
        """Set dashboard data in cache"""
        await self.metrics_cache.set(f"dashboard:{patient_id}", dashboard_data)
    
    async def invalidate_dashboard_data(self, patient_id: str) -> None:
        """Invalidate dashboard data cache"""
        await self.metrics_cache.delete(f"dashboard:{patient_id}")
    
    # Utility methods
    async def clear_all(self) -> None:
        """Clear all caches"""
        await self.user_cache.clear()
        await self.report_cache.clear()
        await self.analysis_cache.clear()
        await self.search_cache.clear()
        await self.metrics_cache.clear()
    
    def get_all_stats(self) -> Dict[str, Dict[str, Any]]:
        """Get statistics for all caches"""
        return {
            "user_cache": self.user_cache.get_stats(),
            "report_cache": self.report_cache.get_stats(),
            "analysis_cache": self.analysis_cache.get_stats(),
            "search_cache": self.search_cache.get_stats(),
            "metrics_cache": self.metrics_cache.get_stats()
        }
    
    def create_search_hash(self, **kwargs) -> str:
        """Create a hash for search parameters"""
        # Sort parameters for consistent hashing
        sorted_params = sorted(kwargs.items())
        params_str = json.dumps(sorted_params, default=str, sort_keys=True)
        return str(hash(params_str))
    
    def create_metrics_hash(self, metrics: list) -> str:
        """Create a hash for metrics list"""
        sorted_metrics = sorted(metrics)
        return str(hash(tuple(sorted_metrics)))


# Global cache manager instance
cache_manager = CacheManager()


def get_cache_manager() -> CacheManager:
    """Get the global cache manager instance"""
    return cache_manager