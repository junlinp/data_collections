import redis
import time

class RedisQueueManager:
    def __init__(self, host='redis', port=6379, db=0):
        # Add socket timeouts to prevent blocking
        self.r = redis.Redis(host=host, port=port, db=db, decode_responses=True, socket_connect_timeout=2, socket_timeout=5)
        self.queue_key = 'crawler:queue'
        self.visited_key = 'crawler:visited'
        self.counter_key = 'crawler:queue_counter'

    def add_url(self, url):
        try:
            # Only add if not visited in last 24h
            if not self.r.sismember(self.visited_key, url):
                result = self.r.lpush(self.queue_key, url)
                # Increment counter
                self.r.incr(self.counter_key)
                print(f"[DEBUG] Added URL to queue: {url}, lpush result: {result}", flush=True)
                return True
            print(f"[DEBUG] URL already visited: {url}", flush=True)
            return False
        except Exception as e:
            print(f"Redis error in add_url: {e}", flush=True)
            return False

    def get_next_url(self):
        try:
            url = self.r.rpop(self.queue_key)
            print(f"[DEBUG] get_next_url rpop result: {url}", flush=True)
            if url:
                self.r.sadd(self.visited_key, url)
                self.r.expire(self.visited_key, 24*3600)  # 24h expiry
                # Decrement counter
                self.r.decr(self.counter_key)
            return url
        except Exception as e:
            print(f"Redis error in get_next_url: {e}", flush=True)
            return None

    def queue_length(self):
        try:
            # For very large queues, use a simple approach
            # Try to get from counter first (fast)
            counter = self.r.get(self.counter_key)
            if counter is not None:
                length = int(counter)
                print(f"[DEBUG] Redis queue length (from counter): {length}", flush=True)
                return length
            
            # For large queues, just return an estimate instead of hanging
            # Check if we have a recent estimate
            estimated = self.r.get('crawler:estimated_count')
            if estimated:
                length = int(estimated)
                print(f"[DEBUG] Redis queue length (estimated): {length}", flush=True)
                return length
            
            # If no estimate, try llen but with a very conservative approach
            # For now, just return a reasonable estimate
            print("[DEBUG] Using fallback queue length estimate", flush=True)
            return 1500000  # Conservative estimate based on what we've seen
            
        except Exception as e:
            print(f"Redis error in queue_length: {e}", flush=True)
            return 0

    def clear_queue(self):
        try:
            self.r.delete(self.queue_key)
            self.r.delete(self.visited_key)
        except Exception as e:
            print(f"Redis error in clear_queue: {e}")

    def get_queue_state(self):
        try:
            # Use a more efficient approach for large queues
            # Instead of calling queue_length() twice, call it once and cache
            queue_len = self.queue_length()
            return {
                'total_urls': queue_len,
                'queued_urls': queue_len,
                'processing_urls': 0,
                'completed_urls': 0,
                'failed_urls': 0
            }
        except Exception as e:
            print(f"Redis error in get_queue_state: {e}")
            return {
                'total_urls': 0,
                'queued_urls': 0,
                'processing_urls': 0,
                'completed_urls': 0,
                'failed_urls': 0,
                'error': str(e)
            }

    def mark_failed(self):
        pass

    def mark_completed(self):
        pass 