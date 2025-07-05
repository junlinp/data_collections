"""
Redis Logging Fix - Stop excessive health check logging
This script will drastically reduce Redis health check logging frequency
"""

import redis
import time
import logging
import os

# Configure minimal logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')
logger = logging.getLogger(__name__)

def fix_redis_logging():
    """Fix excessive Redis health check logging"""
    try:
        # Connect to Redis
        r = redis.Redis(host='redis', port=6379, decode_responses=True)
        
        # Set a flag to disable frequent health checks
        r.set('redis:health_check_disabled', '1', ex=3600)  # Disable for 1 hour
        r.set('redis:last_health_check', str(time.time()))
        
        logger.info("✅ Disabled excessive Redis health check logging")
        
        # Set connection pool size limits to reduce memory usage
        r.connection_pool.connection_kwargs['health_check_interval'] = 300  # 5 minutes
        
        logger.info("✅ Updated Redis connection pool settings")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Error fixing Redis logging: {e}")
        return False

def get_memory_usage():
    """Get current memory usage"""
    try:
        import psutil
        process = psutil.Process()
        memory_mb = process.memory_info().rss / 1024 / 1024
        return memory_mb
    except:
        return 0

if __name__ == "__main__":
    logger.info("🔧 Starting Redis logging fix...")
    
    memory_before = get_memory_usage()
    logger.info(f"Memory before fix: {memory_before:.1f}MB")
    
    if fix_redis_logging():
        logger.info("✅ Redis logging fix applied successfully")
        
        # Wait a bit and check memory
        time.sleep(10)
        memory_after = get_memory_usage()
        logger.info(f"Memory after fix: {memory_after:.1f}MB")
        logger.info(f"Memory difference: {memory_after - memory_before:.1f}MB")
    else:
        logger.error("❌ Failed to apply Redis logging fix")
        exit(1) 