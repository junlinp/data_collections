"""
Fixed Crawler Worker - with duplicate URL adding code removed
This version ensures that discovered links are only added once to the queue
"""

import time
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import threading
import json
import logging
import traceback
import uuid
import redis
import gc
import psutil
from redis_queue_manager import RedisQueueManager
from mongo_utils import get_mongo_manager
from memory_optimizer import html_processor, log_memory_usage, is_memory_critical
import memory_optimizer

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class CrawlerWorker:
    """Worker that processes URLs from the queue"""
    
    def __init__(self, worker_id=None):
        self.worker_id = worker_id or f"worker_{uuid.uuid4().hex[:8]}"
        self.running = False
        self.thread = None
        self.last_activity = time.time()
        self.processed_count = 0
        self.error_count = 0
        self.startup_time = time.time()
        
        logger.info(f"🚀 Initializing worker {self.worker_id}")
        
        # Create a session for better cookie handling
        self.session = requests.Session()
        
        # Configure proxy settings from environment
        import os
        http_proxy = os.environ.get('HTTP_PROXY') or os.environ.get('http_proxy')
        https_proxy = os.environ.get('HTTPS_PROXY') or os.environ.get('https_proxy')
        if http_proxy and https_proxy:
            self.session.proxies = {
                'http': http_proxy,
                'https': https_proxy
            }
            logger.info(f"✅ Worker {self.worker_id} configured proxy: HTTP={http_proxy}, HTTPS={https_proxy}")
        else:
            logger.info(f"Worker {self.worker_id} running without proxy")
        
        # Configure SSL and retry settings for proxy compatibility
        from requests.adapters import HTTPAdapter
        from urllib3.util.retry import Retry
        
        # Configure retry strategy
        retry_strategy = Retry(
            total=3,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)
        
        # Enhanced headers to better mimic a real browser
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8,fr;q=0.7',
            'Accept-Encoding': 'gzip, deflate, br',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Sec-Fetch-User': '?1',
            'Cache-Control': 'max-age=0',
            'Sec-Ch-Ua': '"Chromium";v="124", "Google Chrome";v="124", "Not-A.Brand";v="99"',
            'Sec-Ch-Ua-Mobile': '?0',
            'Sec-Ch-Ua-Platform': '"Windows"',
        })
        
        self.init_content_db()
        
        # Use RedisQueueManager for queue operations
        self.queue = RedisQueueManager(host='redis', port=6379)
        
        self.metrics_key = 'crawler:metrics'
        self.redis = redis.Redis(host='redis', port=6379, decode_responses=True)
        
        logger.info(f"✅ Worker {self.worker_id} initialized successfully")
    
    def log_worker_resources(self):
        """Log worker-specific resource usage"""
        try:
            process = psutil.Process()
            memory_info = process.memory_info()
            
            logger.info(f"WORKER {self.worker_id} RESOURCES - "
                       f"Memory: {memory_info.rss / 1024 / 1024:.2f}MB, "
                       f"Processed: {self.processed_count}, "
                       f"Errors: {self.error_count}, "
                       f"Uptime: {time.time() - self.startup_time:.2f}s, "
                       f"Last activity: {time.time() - self.last_activity:.2f}s ago")
        except Exception as e:
            logger.error(f"Error logging worker resources: {e}")
    
    def init_content_db(self):
        """Initialize the MongoDB connection"""
        try:
            logger.info(f"Worker {self.worker_id}: Initializing MongoDB connection...")
            # Initialize MongoDB manager
            self.mongo_manager = get_mongo_manager()
            
            # Test the connection
            stats = self.mongo_manager.get_database_stats()
            logger.info(f"✅ Worker {self.worker_id}: MongoDB connection successful - stats: {stats}")
        except Exception as e:
            logger.error(f"❌ Worker {self.worker_id}: MongoDB connection failed: {e}")
            logger.error(traceback.format_exc())
            raise
    
    def start(self):
        """Start the worker thread"""
        if self.running:
            logger.warning(f"Worker {self.worker_id} is already running")
            return
        
        logger.info(f"🚀 Starting worker {self.worker_id}")
        self.log_worker_resources()
        
        self.running = True
        self.thread = threading.Thread(target=self._work_loop, daemon=True)
        self.thread.start()
        
        # Initialize worker metrics in Redis
        try:
            self.redis.hset(f'{self.metrics_key}:{self.worker_id}', 'processed_urls', 0)
            self.redis.hset(f'{self.metrics_key}:{self.worker_id}', 'failed_urls', 0)
            self.redis.hset(f'{self.metrics_key}:{self.worker_id}', 'started_at', time.time())
            logger.info(f"✅ Worker {self.worker_id} metrics initialized in Redis")
        except Exception as e:
            logger.error(f"❌ Error initializing worker metrics for {self.worker_id}: {e}")
            logger.error(traceback.format_exc())
        
        logger.info(f"✅ Worker {self.worker_id} started successfully")
    
    def stop(self):
        """Stop the worker thread"""
        logger.info(f"🛑 Stopping worker {self.worker_id}")
        self.log_worker_resources()
        
        self.running = False
        if self.thread:
            self.thread.join(timeout=5)
            if self.thread.is_alive():
                logger.warning(f"Worker {self.worker_id} thread did not stop gracefully")
            else:
                logger.info(f"✅ Worker {self.worker_id} thread stopped gracefully")
        
        # Log final stats
        logger.info(f"Final stats for worker {self.worker_id}: "
                   f"Processed: {self.processed_count}, "
                   f"Errors: {self.error_count}, "
                   f"Runtime: {time.time() - self.startup_time:.2f}s")
    
    def _work_loop(self):
        """Main work loop - continuously processes URLs from queue"""
        logger.info(f"Worker {self.worker_id}: Starting work loop")
        consecutive_errors = 0
        last_resource_log = time.time()
        
        while self.running:
            try:
                # Log resources periodically
                if time.time() - last_resource_log > 300:  # Every 5 minutes
                    self.log_worker_resources()
                    last_resource_log = time.time()
                
                # Get next URL from Redis queue
                url = self.queue.get_next_url()
                if url:
                    logger.info(f"Worker {self.worker_id} processing URL: {url}")
                    self.last_activity = time.time()
                    
                    try:
                        self._process_url(url)
                        self.processed_count += 1
                        consecutive_errors = 0  # Reset error counter on success
                    except Exception as e:
                        self.error_count += 1
                        consecutive_errors += 1
                        logger.error(f"❌ Worker {self.worker_id} error processing {url}: {e}")
                        logger.error(traceback.format_exc())
                        
                        # If too many consecutive errors, take a longer break
                        if consecutive_errors >= 5:
                            logger.error(f"Worker {self.worker_id} has {consecutive_errors} consecutive errors, "
                                       f"taking extended break")
                            time.sleep(30)
                            consecutive_errors = 0
                else:
                    # No URLs in queue, wait a bit
                    time.sleep(1)
                    
            except Exception as e:
                self.error_count += 1
                logger.error(f"❌ Error in work loop for worker {self.worker_id}: {e}")
                logger.error(traceback.format_exc())
                self.log_worker_resources()
                
                # Test connections on major errors
                try:
                    logger.info(f"Worker {self.worker_id}: Testing connections after error...")
                    self.redis.ping()
                    logger.info(f"Worker {self.worker_id}: Redis connection OK")
                    
                    self.mongo_manager.get_database_stats()
                    logger.info(f"Worker {self.worker_id}: MongoDB connection OK")
                except Exception as conn_e:
                    logger.error(f"❌ Worker {self.worker_id} connection test failed: {conn_e}")
                    logger.error(traceback.format_exc())
                
                time.sleep(5)  # Wait before retrying
        
        logger.info(f"Worker {self.worker_id}: Work loop ended")
    
    @memory_optimizer.monitor_memory
    def _process_url(self, url):
        """Process a single URL with step-by-step timing and memory optimization"""
        if not self._should_process_url(url):
            logger.info(f"Worker {self.worker_id} skipping binary/non-HTML URL: {url}")
            return

        with memory_optimizer.memory_managed_processing(f"process_url_{self.worker_id}"):
            timings = {}
            response_time = None
            content_length = None
            error = None
            
            url_start_time = time.time()
            logger.info(f"Worker {self.worker_id}: Starting URL processing: {url}")
            
            # Log memory before processing
            log_memory_usage(f"Worker {self.worker_id} before processing {url}")

            try:
                # Step 1: Fetch URL
                fetch_start = time.time()
                logger.debug(f"Worker {self.worker_id}: Fetching URL: {url}")
                
                # Special handling for Baidu sites
                if 'baidu.com' in url.lower():
                    # Add Baidu-specific headers
                    headers = {
                        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
                        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                        'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
                        'Accept-Encoding': 'gzip, deflate',
                        'Referer': 'https://www.baidu.com/',
                        'Connection': 'keep-alive'
                    }
                    response = self.session.get(url, timeout=60, allow_redirects=True, headers=headers, verify=True)
                else:
                    response = self.session.get(url, timeout=60, allow_redirects=True, verify=True)
                
                fetch_time = time.time() - fetch_start
                timings['fetch'] = fetch_time
                content_length = len(response.content)
                
                logger.debug(f"Worker {self.worker_id}: Fetch completed in {fetch_time:.2f}s, "
                            f"status: {response.status_code}, size: {content_length}")

                if response.status_code == 200:
                    # Step 2: Check content type
                    content_type = response.headers.get('content-type', '').lower()
                    if not any(html_type in content_type for html_type in ['text/html', 'application/xhtml']):
                        logger.info(f"Worker {self.worker_id} skipping non-HTML content: {url} (Content-Type: {content_type})")
                        return

                    # Step 3: Memory-optimized HTML processing
                    parse_start = time.time()
                    logger.debug(f"Worker {self.worker_id}: Processing HTML efficiently for: {url}")
                    
                    # Store HTML content temporarily for LLM processing (limit size to prevent memory issues)
                    self._current_html_content = response.text[:50000] if response.text else ''
                    
                    # Use memory-optimized HTML processing
                    processed_data = html_processor.process_html_efficiently(response.text, url)
                    
                    parse_time = time.time() - parse_start
                    timings['parse'] = parse_time
                    
                    if processed_data:
                        title = processed_data['title']
                        content = processed_data['content']
                        links = processed_data['links']
                        
                        logger.debug(f"Worker {self.worker_id}: HTML processing completed in {parse_time:.2f}s, "
                                   f"title: {title[:50] if title else 'None'}, "
                                   f"content length: {len(content) if content else 0}")
                        
                        # Clear response data immediately to free memory
                        response.close()
                        del response
                        
                        # Force garbage collection if memory is high
                        if is_memory_critical():
                            logger.warning(f"Worker {self.worker_id}: Memory critical, forcing cleanup")
                            gc.collect()

                        # Step 4: Save to DB
                        save_start = time.time()
                        logger.debug(f"Worker {self.worker_id}: Saving to database: {url}")
                        self._save_content_efficiently(url, title, content, links, fetch_time, content_length)
                        save_time = time.time() - save_start
                        timings['save'] = save_time
                        
                        # Clean up HTML content to free memory
                        self._current_html_content = ''
                        
                        # Step 5: Add discovered links (SINGLE OCCURRENCE - NO DUPLICATES)
                        add_links_start = time.time()
                        try:
                            link_count = 0
                            for link in links[:20]:  # Limit to 20 links to reduce memory usage
                                if self.queue.add_url(link):
                                    self.redis.hincrby(self.metrics_key, 'total_urls', 1)
                                    link_count += 1
                            logger.debug(f"Worker {self.worker_id}: Added {link_count} new links to queue")
                        except Exception as e:
                            logger.error(f"❌ Worker {self.worker_id} error adding discovered links for {url}: {e}")
                        
                        add_links_time = time.time() - add_links_start
                        timings['add_links'] = add_links_time

                        # Update metrics
                        self.redis.hincrby(self.metrics_key, 'completed_urls', 1)
                        self.redis.hincrby(f'{self.metrics_key}:{self.worker_id}', 'processed_urls', 1)
                        self.redis.hset(self.metrics_key, 'last_crawled_url', url)
                        
                        total_time = time.time() - url_start_time
                        logger.info(f"✅ Worker {self.worker_id} successfully processed {url} in {total_time:.2f}s")
                        
                        # Log memory after processing
                        log_memory_usage(f"Worker {self.worker_id} after processing {url}")
                        
                    else:
                        logger.error(f"❌ Worker {self.worker_id} failed to process HTML for {url}")
                        error = "HTML processing failed"

                else:
                    self.redis.hincrby(self.metrics_key, 'failed_urls', 1)
                    self.redis.hincrby(f'{self.metrics_key}:{self.worker_id}', 'failed_urls', 1)
                    logger.warning(f"❌ Worker {self.worker_id} failed to process {url}: HTTP {response.status_code}")
                    error = f"HTTP {response.status_code}"

            except requests.exceptions.Timeout as e:
                self.redis.hincrby(self.metrics_key, 'failed_urls', 1)
                self.redis.hincrby(f'{self.metrics_key}:{self.worker_id}', 'failed_urls', 1)
                logger.error(f"❌ Worker {self.worker_id} timeout for {url}: {e}")
                error = f"Timeout: {str(e)}"
            except requests.exceptions.ConnectionError as e:
                self.redis.hincrby(self.metrics_key, 'failed_urls', 1)
                self.redis.hincrby(f'{self.metrics_key}:{self.worker_id}', 'failed_urls', 1)
                logger.error(f"❌ Worker {self.worker_id} connection error for {url}: {e}")
                error = f"Connection error: {str(e)}"
            except requests.exceptions.RequestException as e:
                self.redis.hincrby(self.metrics_key, 'failed_urls', 1)
                self.redis.hincrby(f'{self.metrics_key}:{self.worker_id}', 'failed_urls', 1)
                logger.error(f"❌ Worker {self.worker_id} request error for {url}: {e}")
                error = f"Request error: {str(e)}"
            except Exception as e:
                self.redis.hincrby(self.metrics_key, 'failed_urls', 1)
                self.redis.hincrby(f'{self.metrics_key}:{self.worker_id}', 'failed_urls', 1)
                logger.error(f"❌ Worker {self.worker_id} processing error for {url}: {e}")
                logger.error(traceback.format_exc())
                error = f"Processing error: {str(e)}"

            # Store step timings in Redis (memory-efficient)
            timings_record = {
                'url': url,
                'timestamp': time.time(),
                'timings': timings,
                'error': error,
                'total_time': time.time() - url_start_time
            }
            
            # Only keep recent timing data to save memory
            timings_key = f'{self.metrics_key}:{self.worker_id}:step_times'
            try:
                self.redis.lpush(timings_key, json.dumps(timings_record))
                self.redis.ltrim(timings_key, 0, 49)  # Keep only last 50 (reduced from 100)
            except Exception as e:
                logger.error(f"❌ Worker {self.worker_id} failed to store timing data: {e}")
                
            # Force cleanup periodically
            if self.processed_count % 10 == 0:  # Every 10 URLs
                gc.collect()
                log_memory_usage(f"Worker {self.worker_id} periodic cleanup")
    
    def _save_content_efficiently(self, url, title, content, links, response_time, content_length):
        """Save content with memory optimization"""
        try:
            # Limit content size to prevent memory issues
            max_content_size = 10000  # 10KB max
            if content and len(content) > max_content_size:
                content = content[:max_content_size] + "..."
                logger.debug(f"Truncated content for {url}")
            
            # Save to MongoDB using the manager
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
                
        except Exception as e:
            logger.error(f"Error saving content for {url}: {e}")
    
    def _should_process_url(self, url):
        """Check if URL should be processed (skip binary files and non-HTML content)"""
        # Binary file extensions to skip
        binary_extensions = {
            '.zip', '.tar', '.gz', '.bz2', '.xz', '.7z', '.rar',
            '.exe', '.msi', '.dmg', '.pkg', '.deb', '.rpm',
            '.pdf', '.doc', '.docx', '.xls', '.xlsx', '.ppt', '.pptx',
            '.jpg', '.jpeg', '.png', '.gif', '.bmp', '.svg', '.ico',
            '.mp3', '.mp4', '.avi', '.mov', '.wmv', '.flv', '.mkv',
            '.iso', '.img', '.bin', '.dat', '.db', '.sqlite', '.sqlite3',
            '.jar', '.war', '.ear', '.apk', '.ipa',
            '.pyc', '.pyo', '.so', '.dll', '.dylib', '.a', '.o',
            '.class', '.swf', '.fla', '.psd', '.ai', '.eps',
            '.ttf', '.otf', '.woff', '.woff2', '.eot'
        }
        
        # Check file extension
        parsed_url = urlparse(url)
        path = parsed_url.path.lower()
        
        # Skip if it's a binary file
        for ext in binary_extensions:
            if path.endswith(ext):
                return False
        
        # Skip if it's a data URL or other non-HTTP schemes
        if parsed_url.scheme not in ['http', 'https']:
            return False
        
        # Skip if it's likely a download link (contains download, file, etc.)
        skip_keywords = ['download', 'file', 'attachment', 'binary', 'install']
        url_lower = url.lower()
        for keyword in skip_keywords:
            if keyword in url_lower:
                return False
        
        return True
    
    def _is_same_domain(self, base_url, link_url):
        """Check if link is from the same domain as base URL"""
        try:
            base_domain = urlparse(base_url).netloc.lower()
            link_domain = urlparse(link_url).netloc.lower()
            
            # Handle www vs non-www
            if base_domain.startswith('www.'):
                base_domain = base_domain[4:]
            if link_domain.startswith('www.'):
                link_domain = link_domain[4:]
                
            return base_domain == link_domain
        except Exception as e:
            logger.warning(f"Error checking domain for {link_url}: {e}")
            return False
    
    def get_worker_stats(self):
        """Get worker statistics, including step timing summary"""
        try:
            worker_metrics = self.redis.hgetall(f'{self.metrics_key}:{self.worker_id}')
            processed_count = int(worker_metrics.get('processed_urls', 0))
            failed_count = int(worker_metrics.get('failed_urls', 0))
            started_at = worker_metrics.get('started_at', 0)

            # Step timing summary
            timings_key = f'{self.metrics_key}:{self.worker_id}:step_times'
            timings_list = self.redis.lrange(timings_key, 0, 49)
            step_sums = {}
            step_counts = {}
            step_mins = {}
            step_maxs = {}
            for rec_json in timings_list:
                try:
                    rec = json.loads(rec_json)
                    for step, t in rec.get('timings', {}).items():
                        step_sums[step] = step_sums.get(step, 0.0) + t
                        step_counts[step] = step_counts.get(step, 0) + 1
                        step_mins[step] = min(step_mins.get(step, t), t) if step in step_mins else t
                        step_maxs[step] = max(step_maxs.get(step, t), t) if step in step_maxs else t
                except Exception:
                    continue
            step_summary = {}
            for step in step_sums:
                count = step_counts[step]
                step_summary[step] = {
                    'avg': step_sums[step] / count if count else 0.0,
                    'min': step_mins[step],
                    'max': step_maxs[step],
                    'count': count
                }

            return {
                'worker_id': self.worker_id,
                'running': self.running,
                'processed_urls': processed_count,
                'failed_urls': failed_count,
                'total_urls': processed_count + failed_count,
                'started_at': started_at,
                'thread_alive': self.thread.is_alive() if self.thread else False,
                'step_timings_summary': step_summary
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
                'thread_alive': self.thread.is_alive() if self.thread else False,
                'step_timings_summary': {}
            }

    def add_url_to_queue(self, url):
        if self.queue.add_url(url):
            self.redis.hincrby(self.metrics_key, 'total_urls', 1)
            self.redis.hset(self.metrics_key, 'queue_length', self.queue.queue_length())
            return True
        return False


class WorkerManager:
    """Manages multiple crawler workers"""
    
    def __init__(self, num_workers=2):
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
            worker = CrawlerWorker(worker_id)
            worker.start()
            self.workers[worker_id] = worker
        
        logger.info(f"Started {self.num_workers} workers")
    
    def stop_workers(self):
        """Stop all workers"""
        self.running = False
        
        for worker_id, worker in self.workers.items():
            worker.stop()
        
        self.workers.clear()
        logger.info("Stopped all workers")
    
    def get_worker_stats(self):
        """Get statistics for all workers"""
        stats = {
            'total_workers': len(self.workers),
            'running': self.running,
            'workers': {}
        }
        
        for worker_id, worker in self.workers.items():
            stats['workers'][worker_id] = worker.get_worker_stats()
        
        return stats
    
    def add_worker(self):
        """Add an additional worker"""
        worker_id = f"worker_{len(self.workers) + 1}"
        worker = CrawlerWorker(worker_id)
        worker.start()
        self.workers[worker_id] = worker
        logger.info(f"Added worker {worker_id}")
    
    def remove_worker(self, worker_id):
        """Remove a specific worker"""
        if worker_id in self.workers:
            worker = self.workers[worker_id]
            worker.stop()
            del self.workers[worker_id]
            logger.info(f"Removed worker {worker_id}")


# Global worker manager instance
worker_manager = WorkerManager() 