"""
Crawler Worker - Processes URLs from the queue and extracts data
Runs as a background worker that continuously processes queued URLs
"""

import requests
from bs4 import BeautifulSoup
import threading
import time
import logging
import uuid
from datetime import datetime
from redis_queue_manager import RedisQueueManager
from urllib.parse import urljoin, urlparse
import json
import redis
from mongo_utils import get_mongo_manager

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class CrawlerWorker:
    """Worker that processes URLs from the queue"""
    
    def __init__(self, worker_id=None):
        self.worker_id = worker_id or f"worker_{uuid.uuid4().hex[:8]}"
        self.running = False
        self.thread = None
        
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
            logger.info(f"Configured proxy: HTTP={http_proxy}, HTTPS={https_proxy}")
        
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
        
        logger.info(f"Initialized worker {self.worker_id}")
    
    def init_content_db(self):
        """Initialize the MongoDB connection"""
        try:
            # Initialize MongoDB manager
            self.mongo_manager = get_mongo_manager()
            logger.info(f"Initialized MongoDB connection for worker {self.worker_id}")
        except Exception as e:
            logger.error(f"Error initializing MongoDB for worker {self.worker_id}: {e}")
            raise
    
    def start(self):
        """Start the worker thread"""
        if self.running:
            logger.warning(f"Worker {self.worker_id} is already running")
            return
        
        self.running = True
        self.thread = threading.Thread(target=self._work_loop, daemon=True)
        self.thread.start()
        
        # Initialize worker metrics in Redis
        try:
            self.redis.hset(f'{self.metrics_key}:{self.worker_id}', 'processed_urls', 0)
            self.redis.hset(f'{self.metrics_key}:{self.worker_id}', 'failed_urls', 0)
            self.redis.hset(f'{self.metrics_key}:{self.worker_id}', 'started_at', time.time())
        except Exception as e:
            logger.error(f"Error initializing worker metrics for {self.worker_id}: {e}")
        
        logger.info(f"Started worker {self.worker_id}")
    
    def stop(self):
        """Stop the worker thread"""
        self.running = False
        if self.thread:
            self.thread.join(timeout=5)
        logger.info(f"Stopped worker {self.worker_id}")
    
    def _work_loop(self):
        """Main work loop - continuously processes URLs from queue"""
        while self.running:
            try:
                # Get next URL from Redis queue
                url = self.queue.get_next_url()
                if url:
                    logger.info(f"Worker {self.worker_id} processing URL: {url}")
                    self._process_url(url)
                else:
                    # No URLs in queue, wait a bit
                    time.sleep(1)
                    
            except Exception as e:
                logger.error(f"Error in work loop for worker {self.worker_id}: {e}")
                time.sleep(5)  # Wait before retrying
    
    def _process_url(self, url):
        """Process a single URL with step-by-step timing"""
        if not self._should_process_url(url):
            logger.info(f"Worker {self.worker_id} skipping binary/non-HTML URL: {url}")
            return

        timings = {}
        step_start = time.time()
        response_time = None
        content_length = None
        soup = None
        title = None
        content = None
        links = None
        error = None

        try:
            # Step 1: Fetch URL
            fetch_start = time.time()
            
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

            if response.status_code == 200:
                # Step 2: Check content type
                content_type = response.headers.get('content-type', '').lower()
                if not any(html_type in content_type for html_type in ['text/html', 'application/xhtml']):
                    logger.info(f"Worker {self.worker_id} skipping non-HTML content: {url} (Content-Type: {content_type})")
                    return

                # Step 3: Parse HTML
                parse_start = time.time()
                soup = BeautifulSoup(response.content, 'html.parser')
                parse_time = time.time() - parse_start
                timings['parse'] = parse_time

                # Step 4: Extract data
                extract_start = time.time()
                title = self._extract_title(soup)
                content = self._extract_content(soup)
                # Use current URL domain as base domain for same-domain filtering
                links = self._extract_links(soup, url, url)
                extract_time = time.time() - extract_start
                timings['extract'] = extract_time

                # Step 5: Save to DB
                save_start = time.time()
                self._save_content(url, title, content, response.text, links, fetch_time, content_length)
                save_time = time.time() - save_start
                timings['save'] = save_time

                # Step 6: Add discovered links
                add_links_start = time.time()
                try:
                    for link in json.loads(links):
                        if self.queue.add_url(link):
                            self.redis.hincrby(self.metrics_key, 'total_urls', 1)
                    self.redis.hset(self.metrics_key, 'queue_length', self.queue.queue_length())
                except Exception as e:
                    logger.error(f"Error adding discovered links for {url}: {e}")
                add_links_time = time.time() - add_links_start
                timings['add_links'] = add_links_time

                self.redis.hincrby(self.metrics_key, 'completed_urls', 1)
                self.redis.hincrby(f'{self.metrics_key}:{self.worker_id}', 'processed_urls', 1)
                self.redis.hset(self.metrics_key, 'last_crawled_url', url)
                self.redis.hset(self.metrics_key, 'queue_length', self.queue.queue_length())
                logger.info(f"Worker {self.worker_id} successfully processed {url}")
                logger.info(f"Worker {self.worker_id} DEBUG: About to exit success branch for {url}")

            else:
                self.redis.hincrby(self.metrics_key, 'failed_urls', 1)
                self.redis.hincrby(f'{self.metrics_key}:{self.worker_id}', 'failed_urls', 1)
                self.redis.hset(self.metrics_key, 'queue_length', self.queue.queue_length())
                logger.warning(f"Worker {self.worker_id} failed to process {url}: HTTP error")
                error = "HTTP error"

        except requests.exceptions.RequestException as e:
            self.redis.hincrby(self.metrics_key, 'failed_urls', 1)
            self.redis.hincrby(f'{self.metrics_key}:{self.worker_id}', 'failed_urls', 1)
            self.redis.hset(self.metrics_key, 'queue_length', self.queue.queue_length())
            logger.error(f"Worker {self.worker_id} request error for {url}: {e}")
            error = str(e)
        except Exception as e:
            self.redis.hincrby(self.metrics_key, 'failed_urls', 1)
            self.redis.hincrby(f'{self.metrics_key}:{self.worker_id}', 'failed_urls', 1)
            self.redis.hset(self.metrics_key, 'queue_length', self.queue.queue_length())
            logger.error(f"Worker {self.worker_id} processing error for {url}: {e}")
            error = str(e)

        logger.info(f"Worker {self.worker_id} DEBUG: About to reach timing storage for {url}")
        # Store step timings in Redis (as a capped list, last 100 entries)
        logger.info(f"Worker {self.worker_id} REACHED timing storage section for URL: {url}")
        timings_record = {
            'url': url,
            'timestamp': time.time(),
            'timings': timings,
            'error': error,
        }
        timings_key = f'{self.metrics_key}:{self.worker_id}:step_times'
        try:
            logger.info(f"Worker {self.worker_id} storing timing data for {url}: {timings}")
            self.redis.lpush(timings_key, json.dumps(timings_record))
            self.redis.ltrim(timings_key, 0, 99)  # Keep only last 100
            logger.info(f"Worker {self.worker_id} successfully stored timing data in key: {timings_key}")
        except Exception as e:
            logger.error(f"Worker {self.worker_id} failed to store timing data: {e}")
    
    def _extract_title(self, soup):
        """Extract title from HTML"""
        title_tag = soup.find('title')
        if title_tag:
            return title_tag.get_text().strip()
        return None
    
    def _extract_content(self, soup):
        """Extract main content from HTML"""
        # Remove script and style elements
        for script in soup(["script", "style"]):
            script.decompose()
        
        # Get text content
        text = soup.get_text()
        
        # Clean up whitespace
        lines = (line.strip() for line in text.splitlines())
        chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
        text = ' '.join(chunk for chunk in chunks if chunk)
        
        return text
    
    def _extract_links(self, soup, current_url, base_url):
        """Extract links from HTML - only same domain"""
        links = []
        for link in soup.find_all('a', href=True):
            href = link['href'].strip()
            if not href:
                continue
                
            try:
                absolute_url = urljoin(current_url, href)
            except Exception as e:
                logger.warning(f"Error joining URL {current_url} with {href}: {e}")
                continue
            
            # Filter links - only same domain and processable URLs
            if (not absolute_url.startswith(('javascript:', 'mailto:', '#', 'tel:', 'ftp:')) and
                not absolute_url.endswith(('.pdf', '.jpg', '.jpeg', '.png', '.gif', '.css', '.js', '.xml', '.zip', '.exe')) and
                self._should_process_url(absolute_url) and
                self._is_same_domain(base_url, absolute_url)):
                links.append(absolute_url)
        
        return json.dumps(links)
    
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
    
    def _save_content(self, url, title, content, html_content, links, response_time, content_length):
        """Save crawled content to MongoDB"""
        try:
            # Save to MongoDB using the manager
            success = self.mongo_manager.save_web_content(
                url=url,
                title=title,
                html_content=html_content,
                text_content=content,
                parent_url=None
            )
            
            if success:
                logger.info(f"Successfully saved content for {url} to MongoDB")
            else:
                logger.error(f"Failed to save content for {url} to MongoDB")
                
        except Exception as e:
            logger.error(f"Error saving content for {url} to MongoDB: {e}")
    
    def get_worker_stats(self):
        """Get worker statistics, including step timing summary"""
        try:
            worker_metrics = self.redis.hgetall(f'{self.metrics_key}:{self.worker_id}')
            processed_count = int(worker_metrics.get('processed_urls', 0))
            failed_count = int(worker_metrics.get('failed_urls', 0))
            started_at = worker_metrics.get('started_at', 0)

            # Step timing summary
            timings_key = f'{self.metrics_key}:{self.worker_id}:step_times'
            timings_list = self.redis.lrange(timings_key, 0, 99)
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