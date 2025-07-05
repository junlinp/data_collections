"""
Memory-Optimized Crawler Worker - Processes URLs from the queue with memory management
Enhanced with memory optimization to prevent high memory usage issues
"""

import requests
import threading
import time
import logging
import uuid
import sys
import traceback
import psutil
import signal
import gc
import json
import redis
from datetime import datetime
from redis_queue_manager import RedisQueueManager
from urllib.parse import urljoin, urlparse
from mongo_utils import get_mongo_manager
from memory_optimizer import memory_optimizer, html_processor, log_memory_usage, is_memory_critical

# Configure logging
logging.basicConfig(
    level=logging.INFO, 
    format='%(asctime)s - %(name)s - %(levelname)s - [PID:%(process)d] - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('/app/data/crawler_worker.log', mode='a')
    ]
)
logger = logging.getLogger(__name__)

class MemoryOptimizedCrawlerWorker:
    """Memory-optimized crawler worker with advanced memory management"""
    
    def __init__(self, worker_id=None):
        self.worker_id = worker_id or f"worker_{uuid.uuid4().hex[:8]}"
        self.running = False
        self.thread = None
        self.last_activity = time.time()
        self.processed_count = 0
        self.error_count = 0
        self.startup_time = time.time()
        
        logger.info(f"🚀 Initializing memory-optimized worker {self.worker_id}")
        
        # Create session with connection pooling limits
        self.session = requests.Session()
        
        # Limit connection pool size to reduce memory usage
        from requests.adapters import HTTPAdapter
        from urllib3.util.retry import Retry
        
        retry_strategy = Retry(
            total=2,  # Reduced retries to save memory
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
        )
        adapter = HTTPAdapter(max_retries=retry_strategy, pool_connections=10, pool_maxsize=10)
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)
        
        # Minimal headers to reduce memory usage
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'DNT': '1',
            'Connection': 'keep-alive'
        })
        
        self.init_content_db()
        self.queue = RedisQueueManager(host='redis', port=6379)
        self.metrics_key = 'crawler:metrics'
        self.redis = redis.Redis(host='redis', port=6379, decode_responses=True)
        
        logger.info(f"✅ Memory-optimized worker {self.worker_id} initialized")
    
    def init_content_db(self):
        """Initialize MongoDB connection"""
        try:
            logger.info(f"Worker {self.worker_id}: Initializing MongoDB connection...")
            self.mongo_manager = get_mongo_manager()
            
            # Test connection
            stats = self.mongo_manager.get_database_stats()
            logger.info(f"✅ Worker {self.worker_id}: MongoDB connection successful")
        except Exception as e:
            logger.error(f"❌ Worker {self.worker_id}: MongoDB connection failed: {e}")
            raise
    
    def start(self):
        """Start the worker thread"""
        if self.running:
            logger.warning(f"Worker {self.worker_id} is already running")
            return
        
        logger.info(f"🚀 Starting memory-optimized worker {self.worker_id}")
        log_memory_usage(f"Worker {self.worker_id} startup")
        
        self.running = True
        self.thread = threading.Thread(target=self._work_loop, daemon=True)
        self.thread.start()
        
        # Initialize worker metrics in Redis
        try:
            self.redis.hset(f'{self.metrics_key}:{self.worker_id}', 'processed_urls', 0)
            self.redis.hset(f'{self.metrics_key}:{self.worker_id}', 'failed_urls', 0)
            self.redis.hset(f'{self.metrics_key}:{self.worker_id}', 'started_at', time.time())
            logger.info(f"✅ Worker {self.worker_id} metrics initialized")
        except Exception as e:
            logger.error(f"❌ Error initializing worker metrics: {e}")
        
        logger.info(f"✅ Worker {self.worker_id} started successfully")
    
    def stop(self):
        """Stop the worker thread"""
        logger.info(f"🛑 Stopping worker {self.worker_id}")
        log_memory_usage(f"Worker {self.worker_id} stopping")
        
        self.running = False
        if self.thread:
            self.thread.join(timeout=5)
            if self.thread.is_alive():
                logger.warning(f"Worker {self.worker_id} thread did not stop gracefully")
            else:
                logger.info(f"✅ Worker {self.worker_id} thread stopped gracefully")
        
        # Final cleanup
        try:
            self.session.close()
            gc.collect()
            log_memory_usage(f"Worker {self.worker_id} final cleanup")
        except Exception as e:
            logger.error(f"Error during worker cleanup: {e}")
    
    def _work_loop(self):
        """Main work loop with memory management"""
        logger.info(f"Worker {self.worker_id}: Starting memory-optimized work loop")
        consecutive_errors = 0
        last_resource_log = time.time()
        
        while self.running:
            try:
                # Log resources periodically
                if time.time() - last_resource_log > 300:  # Every 5 minutes
                    log_memory_usage(f"Worker {self.worker_id} periodic check")
                    last_resource_log = time.time()
                
                # Get next URL from Redis queue
                url = self.queue.get_next_url()
                if url:
                    logger.info(f"Worker {self.worker_id} processing URL: {url}")
                    self.last_activity = time.time()
                    
                    try:
                        self._process_url_optimized(url)
                        self.processed_count += 1
                        consecutive_errors = 0
                    except Exception as e:
                        self.error_count += 1
                        consecutive_errors += 1
                        logger.error(f"❌ Worker {self.worker_id} error processing {url}: {e}")
                        
                        # If too many consecutive errors, take a longer break
                        if consecutive_errors >= 5:
                            logger.error(f"Worker {self.worker_id} has {consecutive_errors} consecutive errors, taking extended break")
                            time.sleep(30)
                            consecutive_errors = 0
                else:
                    # No URLs in queue, wait a bit
                    time.sleep(1)
                    
            except Exception as e:
                self.error_count += 1
                logger.error(f"❌ Error in work loop for worker {self.worker_id}: {e}")
                logger.error(traceback.format_exc())
                
                # Wait before continuing
                time.sleep(5)
        
        logger.info(f"Worker {self.worker_id}: Work loop ended")
    
    @memory_optimizer.monitor_memory
    def _process_url_optimized(self, url):
        """Process URL with comprehensive memory optimization"""
        if not self._should_process_url(url):
            logger.debug(f"Worker {self.worker_id} skipping non-processable URL: {url}")
            return

        with memory_optimizer.memory_managed_processing(f"process_url_{self.worker_id}"):
            timings = {}
            error = None
            
            url_start_time = time.time()
            logger.debug(f"Worker {self.worker_id}: Starting URL processing: {url}")
            
            # Log memory before processing
            log_memory_usage(f"Worker {self.worker_id} before processing")

            try:
                # Step 1: Fetch URL with memory optimization
                fetch_start = time.time()
                response = self._fetch_url_efficiently(url)
                fetch_time = time.time() - fetch_start
                timings['fetch'] = fetch_time
                
                if response and response.status_code == 200:
                    # Check content type
                    content_type = response.headers.get('content-type', '').lower()
                    if not any(html_type in content_type for html_type in ['text/html', 'application/xhtml']):
                        logger.debug(f"Worker {self.worker_id} skipping non-HTML content: {url}")
                        return

                    # Step 2: Memory-optimized HTML processing
                    parse_start = time.time()
                    # Store HTML content temporarily for LLM processing (limit size to prevent memory issues)
                    self._current_html_content = response.text[:50000] if response.text else ''
                    processed_data = html_processor.process_html_efficiently(response.text, url)
                    parse_time = time.time() - parse_start
                    timings['parse'] = parse_time
                    
                    # Clear response immediately to free memory
                    response.close()
                    del response
                    
                    if processed_data:
                        title = processed_data['title']
                        content = processed_data['content']
                        links = processed_data['links']
                        
                        logger.debug(f"Worker {self.worker_id}: HTML processing completed in {parse_time:.2f}s")
                        
                        # Force garbage collection if memory is critical
                        if is_memory_critical():
                            logger.warning(f"Worker {self.worker_id}: Memory critical, forcing cleanup")
                            gc.collect()

                        # Step 3: Save to DB efficiently
                        save_start = time.time()
                        self._save_content_efficiently(url, title, content, links)
                        save_time = time.time() - save_start
                        timings['save'] = save_time
                        
                        # Clean up HTML content to free memory
                        self._current_html_content = ''
                        
                        # Step 4: Add discovered links (limited to prevent memory bloat)
                        add_links_start = time.time()
                        link_count = self._add_links_efficiently(links)
                        add_links_time = time.time() - add_links_start
                        timings['add_links'] = add_links_time

                        # Update metrics
                        self.redis.hincrby(self.metrics_key, 'completed_urls', 1)
                        self.redis.hincrby(f'{self.metrics_key}:{self.worker_id}', 'processed_urls', 1)
                        self.redis.hset(self.metrics_key, 'last_crawled_url', url)
                        
                        total_time = time.time() - url_start_time
                        logger.info(f"✅ Worker {self.worker_id} processed {url} in {total_time:.2f}s")
                        
                        # Log memory after processing
                        log_memory_usage(f"Worker {self.worker_id} after processing")
                        
                    else:
                        logger.error(f"❌ Worker {self.worker_id} failed to process HTML for {url}")
                        error = "HTML processing failed"
                        self._update_failed_metrics(url, error)

                else:
                    status_code = response.status_code if response else "No response"
                    logger.warning(f"❌ Worker {self.worker_id} failed to fetch {url}: {status_code}")
                    error = f"HTTP {status_code}"
                    self._update_failed_metrics(url, error)

            except Exception as e:
                logger.error(f"❌ Worker {self.worker_id} processing error for {url}: {e}")
                error = f"Processing error: {str(e)}"
                self._update_failed_metrics(url, error)

            # Store limited timing data to save memory
            self._store_timing_data_efficiently(url, timings, error, time.time() - url_start_time)
            
            # Periodic cleanup to prevent memory buildup
            if self.processed_count % 10 == 0:
                gc.collect()
                log_memory_usage(f"Worker {self.worker_id} periodic cleanup")
    
    def _fetch_url_efficiently(self, url):
        """Fetch URL with memory optimization"""
        try:
            # Use stream=True to control memory usage for large files
            response = self.session.get(url, timeout=30, stream=True)
            
            # Check content length to avoid loading huge files
            content_length = response.headers.get('content-length')
            if content_length and int(content_length) > 1000000:  # 1MB limit
                logger.warning(f"Skipping large file: {url} ({content_length} bytes)")
                response.close()
                return None
            
            # Read content in chunks to control memory usage
            content = b''
            chunk_size = 8192
            max_size = 500000  # 500KB max
            
            for chunk in response.iter_content(chunk_size=chunk_size):
                if chunk:
                    content += chunk
                    if len(content) > max_size:
                        logger.warning(f"Truncating large response: {url}")
                        break
            
            # Create new response object with limited content
            response._content = content
            return response
            
        except Exception as e:
            logger.error(f"Error fetching {url}: {e}")
            return None
    
    def _save_content_efficiently(self, url, title, content, links):
        """Save content with memory optimization"""
        try:
            # Limit content size to prevent memory issues
            max_content_size = 10000  # 10KB max
            if content and len(content) > max_content_size:
                content = content[:max_content_size] + "..."
                logger.debug(f"Truncated content for {url}")
            
            # Include HTML content for LLM processing (limited size)
            success = self.mongo_manager.save_web_content(
                url=url,
                title=title or '',
                html_content=getattr(self, '_current_html_content', ''),  # Include HTML for LLM processing
                text_content=content or '',
                parent_url=None
            )
            
            if success:
                logger.debug(f"Successfully saved content for {url}")
            else:
                logger.error(f"Failed to save content for {url}")
                
            return success
            
        except Exception as e:
            logger.error(f"Error saving content for {url}: {e}")
            return False
    
    def _add_links_efficiently(self, links):
        """Add discovered links with memory optimization"""
        try:
            link_count = 0
            # Limit to 10 links per page to prevent memory bloat
            for link in links[:10]:
                if self.queue.add_url(link):
                    self.redis.hincrby(self.metrics_key, 'total_urls', 1)
                    link_count += 1
            
            logger.debug(f"Added {link_count} new links to queue")
            return link_count
            
        except Exception as e:
            logger.error(f"Error adding links: {e}")
            return 0
    
    def _update_failed_metrics(self, url, error):
        """Update failure metrics"""
        try:
            self.redis.hincrby(self.metrics_key, 'failed_urls', 1)
            self.redis.hincrby(f'{self.metrics_key}:{self.worker_id}', 'failed_urls', 1)
        except Exception as e:
            logger.error(f"Error updating failed metrics: {e}")
    
    def _store_timing_data_efficiently(self, url, timings, error, total_time):
        """Store timing data with memory limits"""
        try:
            timings_record = {
                'url': url,
                'timestamp': time.time(),
                'timings': timings,
                'error': error,
                'total_time': total_time
            }
            
            # Only keep last 25 timing records (reduced from 100)
            timings_key = f'{self.metrics_key}:{self.worker_id}:step_times'
            self.redis.lpush(timings_key, json.dumps(timings_record))
            self.redis.ltrim(timings_key, 0, 24)  # Keep only last 25
            
        except Exception as e:
            logger.error(f"Error storing timing data: {e}")
    
    def _should_process_url(self, url):
        """Check if URL should be processed"""
        # Binary file extensions to skip
        binary_extensions = {
            '.zip', '.tar', '.gz', '.bz2', '.rar', '.exe', '.msi', '.dmg', '.pkg',
            '.pdf', '.doc', '.docx', '.xls', '.xlsx', '.ppt', '.pptx',
            '.jpg', '.jpeg', '.png', '.gif', '.bmp', '.svg', '.ico',
            '.mp3', '.mp4', '.avi', '.mov', '.wmv', '.flv', '.mkv'
        }
        
        parsed_url = urlparse(url)
        path = parsed_url.path.lower()
        
        # Skip if it's a binary file
        for ext in binary_extensions:
            if path.endswith(ext):
                return False
        
        # Skip if it's not HTTP/HTTPS
        if parsed_url.scheme not in ['http', 'https']:
            return False
        
        return True
    
    def get_worker_stats(self):
        """Get worker statistics"""
        try:
            worker_metrics = self.redis.hgetall(f'{self.metrics_key}:{self.worker_id}')
            processed_count = int(worker_metrics.get('processed_urls', 0))
            failed_count = int(worker_metrics.get('failed_urls', 0))
            started_at = worker_metrics.get('started_at', 0)

            return {
                'worker_id': self.worker_id,
                'running': self.running,
                'processed_urls': processed_count,
                'failed_urls': failed_count,
                'total_urls': processed_count + failed_count,
                'started_at': started_at,
                'thread_alive': self.thread.is_alive() if self.thread else False,
                'memory_optimized': True
            }
        except Exception as e:
            logger.error(f"Error getting worker stats: {e}")
            return {
                'worker_id': self.worker_id,
                'running': self.running,
                'processed_urls': 0,
                'failed_urls': 0,
                'total_urls': 0,
                'started_at': 0,
                'thread_alive': False,
                'memory_optimized': True
            }


class MemoryOptimizedWorkerManager:
    """Memory-optimized worker manager"""
    
    def __init__(self, num_workers=1):  # Reduced default workers
        self.num_workers = num_workers
        self.workers = {}
        self.running = False
    
    def start_workers(self):
        """Start all workers"""
        if self.running:
            logger.warning("Worker manager is already running")
            return
        
        self.running = True
        
        for i in range(self.num_workers):
            worker_id = f"worker_{i+1}"
            worker = MemoryOptimizedCrawlerWorker(worker_id)
            worker.start()
            self.workers[worker_id] = worker
        
        logger.info(f"Started {self.num_workers} memory-optimized workers")
    
    def stop_workers(self):
        """Stop all workers"""
        self.running = False
        
        for worker_id, worker in self.workers.items():
            worker.stop()
        
        self.workers.clear()
        
        # Force cleanup
        gc.collect()
        logger.info("Stopped all memory-optimized workers")
    
    def get_worker_stats(self):
        """Get statistics for all workers"""
        stats = {
            'total_workers': len(self.workers),
            'running': self.running,
            'workers': {},
            'memory_optimized': True
        }
        
        for worker_id, worker in self.workers.items():
            stats['workers'][worker_id] = worker.get_worker_stats()
        
        return stats
    
    def add_worker(self):
        """Add an additional worker"""
        worker_id = f"worker_{len(self.workers) + 1}"
        worker = MemoryOptimizedCrawlerWorker(worker_id)
        worker.start()
        self.workers[worker_id] = worker
        logger.info(f"Added memory-optimized worker {worker_id}")
    
    def remove_worker(self, worker_id):
        """Remove a specific worker"""
        if worker_id in self.workers:
            worker = self.workers[worker_id]
            worker.stop()
            del self.workers[worker_id]
            logger.info(f"Removed memory-optimized worker {worker_id}")
            
            # Force cleanup after removing worker
            gc.collect()
            log_memory_usage("After removing worker")


# Global memory-optimized worker manager instance
memory_optimized_worker_manager = MemoryOptimizedWorkerManager(num_workers=1)  # Start with 1 worker 