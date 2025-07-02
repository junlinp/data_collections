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
        """Process a single URL"""
        # Skip binary files and non-HTML content
        if not self._should_process_url(url):
            logger.info(f"Worker {self.worker_id} skipping binary/non-HTML URL: {url}")
            return
        
        start_time = time.time()
        status_code = None
        response_time = None
        content_length = None
        
        try:
            # Make request
            response = self.session.get(url, timeout=30, allow_redirects=True)
            response_time = time.time() - start_time
            status_code = response.status_code
            content_length = len(response.content)
            
            if response.status_code == 200:
                # Check content type to ensure it's HTML
                content_type = response.headers.get('content-type', '').lower()
                if not any(html_type in content_type for html_type in ['text/html', 'application/xhtml']):
                    logger.info(f"Worker {self.worker_id} skipping non-HTML content: {url} (Content-Type: {content_type})")
                    return
                
                # Parse content
                soup = BeautifulSoup(response.content, 'html.parser')
                
                # Extract data
                title = self._extract_title(soup)
                content = self._extract_content(soup)
                links = self._extract_links(soup, url)
                
                # Save to database
                self._save_content(url, title, content, response.text, links, status_code, response_time, content_length)
                
                # Add discovered links to the queue for continuous crawling
                try:
                    for link in json.loads(links):
                        if self.queue.add_url(link):
                            self.redis.hincrby(self.metrics_key, 'total_urls', 1)
                    self.redis.hset(self.metrics_key, 'queue_length', self.queue.queue_length())
                except Exception as e:
                    logger.error(f"Error adding discovered links for {url}: {e}")
                
                self.redis.hincrby(self.metrics_key, 'completed_urls', 1)
                self.redis.hincrby(f'{self.metrics_key}:{self.worker_id}', 'processed_urls', 1)
                self.redis.hset(self.metrics_key, 'last_crawled_url', url)
                self.redis.hset(self.metrics_key, 'queue_length', self.queue.queue_length())
                logger.info(f"Worker {self.worker_id} successfully processed {url}")
                
            else:
                # HTTP error
                self.redis.hincrby(self.metrics_key, 'failed_urls', 1)
                self.redis.hincrby(f'{self.metrics_key}:{self.worker_id}', 'failed_urls', 1)
                self.redis.hset(self.metrics_key, 'queue_length', self.queue.queue_length())
                logger.warning(f"Worker {self.worker_id} failed to process {url}: HTTP {response.status_code}")
                
        except requests.exceptions.RequestException as e:
            # Network error
            self.redis.hincrby(self.metrics_key, 'failed_urls', 1)
            self.redis.hincrby(f'{self.metrics_key}:{self.worker_id}', 'failed_urls', 1)
            self.redis.hset(self.metrics_key, 'queue_length', self.queue.queue_length())
            logger.error(f"Worker {self.worker_id} request error for {url}: {e}")
            
        except Exception as e:
            # Other error
            self.redis.hincrby(self.metrics_key, 'failed_urls', 1)
            self.redis.hincrby(f'{self.metrics_key}:{self.worker_id}', 'failed_urls', 1)
            self.redis.hset(self.metrics_key, 'queue_length', self.queue.queue_length())
            logger.error(f"Worker {self.worker_id} processing error for {url}: {e}")
    
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
    
    def _extract_links(self, soup, base_url):
        """Extract links from HTML"""
        links = []
        for link in soup.find_all('a', href=True):
            href = link['href']
            absolute_url = urljoin(base_url, href)
            
            # Only add links that should be processed
            if self._should_process_url(absolute_url):
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
    
    def _save_content(self, url, title, content, html_content, links, status_code, response_time, content_length):
        """Save crawled content to MongoDB"""
        try:
            # Save to MongoDB using the manager
            success = self.mongo_manager.save_web_content(
                url=url,
                title=title,
                html_content=html_content,
                text_content=content,
                status_code=status_code,
                crawl_depth=0,
                parent_url=None
            )
            
            if success:
                logger.info(f"Successfully saved content for {url} to MongoDB")
            else:
                logger.error(f"Failed to save content for {url} to MongoDB")
                
        except Exception as e:
            logger.error(f"Error saving content for {url} to MongoDB: {e}")
    
    def get_worker_stats(self):
        """Get worker statistics"""
        try:
            # Get worker metrics from Redis (more efficient than database query)
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
                'thread_alive': self.thread.is_alive() if self.thread else False
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
                'thread_alive': self.thread.is_alive() if self.thread else False
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