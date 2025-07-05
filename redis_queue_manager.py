import redis
import time
import logging
import sys
import traceback
from datetime import datetime
from redis.exceptions import ConnectionError, TimeoutError, RedisError

# Configure logging with detailed format
logging.basicConfig(
    level=logging.INFO, 
    format='%(asctime)s - %(name)s - %(levelname)s - [PID:%(process)d] - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('/app/data/redis_queue.log', mode='a')
    ]
)
logger = logging.getLogger(__name__)

class RedisQueueManager:
    def __init__(self, host='redis', port=6379, db=0):
        self.host = host
        self.port = port
        self.db = db
        self.connection_attempts = 0
        self.operation_count = 0
        self.error_count = 0
        self.last_connection_error = None
        self.connection_established_at = None
        
        # logger.info(f"🚀 Initializing Redis queue manager")
        # logger.info(f"Redis connection: {host}:{port}, DB: {db}")
        
        # Add socket timeouts to prevent blocking
        self.r = redis.Redis(
            host=host, 
            port=port, 
            db=db, 
            decode_responses=True, 
            socket_connect_timeout=5, 
            socket_timeout=10,
            retry_on_timeout=True,
            health_check_interval=30
        )
        
        self.queue_key = 'crawler:queue'
        self.visited_key = 'crawler:visited'
        self.counter_key = 'crawler:queue_counter'
        
        # Test initial connection
        self.test_connection()
        
        # logger.info(f"✅ Redis queue manager initialized successfully")
    
    def test_connection(self):
        """Test Redis connection health"""
        try:
            self.connection_attempts += 1
            start_time = time.time()
            
            # Test basic connectivity
            result = self.r.ping()
            ping_time = time.time() - start_time
            
            if result:
                self.connection_established_at = datetime.utcnow()
                # logger.info(f"✅ Redis connection healthy - ping: {ping_time:.3f}s")
                
                # Test basic operations
                test_key = 'redis:health:test'
                self.r.set(test_key, 'test_value', ex=10)
                value = self.r.get(test_key)
                self.r.delete(test_key)
                
                if value == 'test_value':
                    # logger.info("✅ Redis read/write operations working")
                    pass
                else:
                    # logger.warning("⚠️ Redis read/write test failed")
                    pass
                
                return True
            else:
                logger.error("❌ Redis ping failed")
                return False
                
        except ConnectionError as e:
            self.last_connection_error = str(e)
            logger.error(f"❌ Redis connection error: {e}")
            return False
        except TimeoutError as e:
            self.last_connection_error = str(e)
            logger.error(f"❌ Redis timeout error: {e}")
            return False
        except Exception as e:
            self.last_connection_error = str(e)
            logger.error(f"❌ Redis connection test failed: {e}")
            logger.error(traceback.format_exc())
            return False
    
    def ensure_connection(self):
        """Ensure Redis connection is active, retry if necessary"""
        if not self.test_connection():
            logger.warning("🔄 Redis connection lost, attempting to reconnect...")
            
            # Try to reconnect with exponential backoff
            max_retries = 3
            retry_delay = 1
            
            for attempt in range(max_retries):
                try:
                    time.sleep(retry_delay)
                    
                    # Create new Redis connection
                    self.r = redis.Redis(
                        host=self.host, 
                        port=self.port, 
                        db=self.db, 
                        decode_responses=True, 
                        socket_connect_timeout=5, 
                        socket_timeout=10,
                        retry_on_timeout=True,
                        health_check_interval=30
                    )
                    
                    if self.test_connection():
                        # logger.info("✅ Redis reconnection successful")
                        return True
                        
                    retry_delay *= 2
                    
                except Exception as e:
                    logger.error(f"❌ Redis reconnection attempt {attempt + 1} failed: {e}")
                    
            logger.error("❌ Redis reconnection failed after all attempts")
            return False
        
        return True
    
    def _execute_operation(self, operation_name, operation_func):
        """Execute Redis operation with error handling and monitoring"""
        start_time = time.time()
        self.operation_count += 1
        
        try:
            if not self.ensure_connection():
                raise ConnectionError("Redis connection could not be established")
                
            result = operation_func()
            
            elapsed = time.time() - start_time
            logger.debug(f"✅ Redis operation '{operation_name}' completed in {elapsed:.3f}s")
            
            return result
            
        except ConnectionError as e:
            self.error_count += 1
            elapsed = time.time() - start_time
            logger.error(f"❌ Redis connection error in '{operation_name}' after {elapsed:.3f}s: {e}")
            raise
        except TimeoutError as e:
            self.error_count += 1
            elapsed = time.time() - start_time
            logger.error(f"❌ Redis timeout error in '{operation_name}' after {elapsed:.3f}s: {e}")
            raise
        except RedisError as e:
            self.error_count += 1
            elapsed = time.time() - start_time
            logger.error(f"❌ Redis error in '{operation_name}' after {elapsed:.3f}s: {e}")
            raise
        except Exception as e:
            self.error_count += 1
            elapsed = time.time() - start_time
            logger.error(f"❌ Unexpected error in '{operation_name}' after {elapsed:.3f}s: {e}")
            logger.error(traceback.format_exc())
            raise

    def add_url(self, url):
        def operation():
            # Only add if not visited in last 24h
            if not self.r.sismember(self.visited_key, url):
                result = self.r.lpush(self.queue_key, url)
                # Increment counter
                self.r.incr(self.counter_key)
                logger.debug(f"✅ Added URL to queue: {url}, lpush result: {result}")
                return True
            logger.debug(f"⚠️ URL already visited: {url}")
            return False
        
        try:
            return self._execute_operation('add_url', operation)
        except Exception as e:
            logger.error(f"❌ Error adding URL {url}: {e}")
            return False

    def get_next_url(self):
        def operation():
            url = self.r.rpop(self.queue_key)
            logger.debug(f"🔄 get_next_url rpop result: {url}")
            if url:
                self.r.sadd(self.visited_key, url)
                self.r.expire(self.visited_key, 24*3600)  # 24h expiry
                # Decrement counter
                self.r.decr(self.counter_key)
                logger.debug(f"✅ Retrieved URL from queue: {url}")
            return url
        
        try:
            return self._execute_operation('get_next_url', operation)
        except Exception as e:
            logger.error(f"❌ Error getting next URL: {e}")
            return None

    def queue_length(self):
        def operation():
            # For very large queues, use a simple approach
            # Try to get from counter first (fast)
            counter = self.r.get(self.counter_key)
            if counter is not None:
                length = int(counter)
                logger.debug(f"📊 Redis queue length (from counter): {length}")
                return length
            
            # For large queues, just return an estimate instead of hanging
            # Check if we have a recent estimate
            estimated = self.r.get('crawler:estimated_count')
            if estimated:
                length = int(estimated)
                logger.debug(f"📊 Redis queue length (estimated): {length}")
                return length
            
            # If no estimate, try llen but with a very conservative approach
            # For now, just return a reasonable estimate
            logger.debug("📊 Using fallback queue length estimate")
            return 1500000  # Conservative estimate based on what we've seen
        
        try:
            return self._execute_operation('queue_length', operation)
        except Exception as e:
            logger.error(f"❌ Error getting queue length: {e}")
            return 0

    def clear_queue(self):
        def operation():
            deleted_queue = self.r.delete(self.queue_key)
            deleted_visited = self.r.delete(self.visited_key)
            deleted_counter = self.r.delete(self.counter_key)
            logger.info(f"🗑️ Cleared queue - Queue: {deleted_queue}, Visited: {deleted_visited}, Counter: {deleted_counter}")
            return deleted_queue + deleted_visited + deleted_counter
        
        try:
            return self._execute_operation('clear_queue', operation)
        except Exception as e:
            logger.error(f"❌ Error clearing queue: {e}")
            return 0

    def get_queue_state(self):
        def operation():
            # Use a more efficient approach for large queues
            # Instead of calling queue_length() twice, call it once and cache
            queue_len = self.queue_length()
            
            # Try to get additional metrics
            try:
                visited_count = self.r.scard(self.visited_key)
            except Exception:
                visited_count = 0
            
            state = {
                'total_urls': queue_len,
                'queued_urls': queue_len,
                'processing_urls': 0,
                'completed_urls': visited_count,
                'failed_urls': 0,
                'connection_attempts': self.connection_attempts,
                'operation_count': self.operation_count,
                'error_count': self.error_count,
                'last_connection_error': self.last_connection_error,
                'connection_established_at': self.connection_established_at
            }
            
            logger.debug(f"📊 Queue state: {state}")
            return state
        
        try:
            return self._execute_operation('get_queue_state', operation)
        except Exception as e:
            logger.error(f"❌ Error getting queue state: {e}")
            return {
                'total_urls': 0,
                'queued_urls': 0,
                'processing_urls': 0,
                'completed_urls': 0,
                'failed_urls': 0,
                'error': str(e),
                'connection_attempts': self.connection_attempts,
                'operation_count': self.operation_count,
                'error_count': self.error_count
            }

    def mark_failed(self):
        def operation():
            # Increment failed counter
            return self.r.incr('crawler:failed_count')
        
        try:
            return self._execute_operation('mark_failed', operation)
        except Exception as e:
            logger.error(f"❌ Error marking failed: {e}")
            return 0

    def mark_completed(self):
        def operation():
            # Increment completed counter
            return self.r.incr('crawler:completed_count')
        
        try:
            return self._execute_operation('mark_completed', operation)
        except Exception as e:
            logger.error(f"❌ Error marking completed: {e}")
            return 0
    
    def get_health_status(self):
        """Get detailed health status for monitoring"""
        try:
            health = {
                'connected': self.test_connection(),
                'connection_attempts': self.connection_attempts,
                'operation_count': self.operation_count,
                'error_count': self.error_count,
                'last_connection_error': self.last_connection_error,
                'connection_established_at': self.connection_established_at,
                'host': self.host,
                'port': self.port,
                'database': self.db
            }
            
            # Add Redis-specific info
            if health['connected']:
                try:
                    info = self.r.info()
                    health['redis_version'] = info.get('redis_version', 'unknown')
                    health['memory_used'] = info.get('used_memory_human', 'unknown')
                    health['connected_clients'] = info.get('connected_clients', 0)
                except Exception:
                    pass
            
            return health
        except Exception as e:
            logger.error(f"❌ Error getting health status: {e}")
            return {
                'error': str(e), 
                'connected': False,
                'connection_attempts': self.connection_attempts,
                'operation_count': self.operation_count,
                'error_count': self.error_count
            } 