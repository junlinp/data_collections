"""
Main crawling logic for the web crawler
Separated from the web interface for better maintainability
"""

import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import sqlite3
from datetime import datetime
import re
import time
from collections import deque
from url_manager import URLManager
import logging
import json
import threading

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class GlobalQueue:
    """Global queue system for managing URLs across crawler instances"""
    
    def __init__(self):
        self.lock = threading.Lock()
        self.queue = deque()
        self.queue_urls = set()
    
    def add_url(self, url, priority=0):
        """Add URL to global queue"""
        with self.lock:
            if url not in self.queue_urls:
                self.queue.append((url, priority))
                self.queue_urls.add(url)
                return True
            return False
    
    def get_next_url(self) -> str | None:
        """Get next URL from queue for processing"""
        with self.lock:
            if len(self.queue) == 0:
                return None
            url, _= self.queue.popleft()
            self.queue_urls.remove(url)
            print(f"Getting next URL: {url}")
            return url
                    
    def get_queue_state(self):
        """Get current queue state"""
        with self.lock:
            return {
                'total_urls': len(self.queue),
                'queued_urls': len(self.queue),
                'processing_urls': 0,
                'completed_urls': 0,
                'failed_urls': 0
            }
                
    def clear_queue(self):
        """Clear queue"""
        with self.lock:
            self.queue = deque()
            self.queue_urls = set()
                
 
# Global queue instance
global_queue = GlobalQueue()

class WebCrawler:
    def __init__(self, content_db_path='web_crawler.db', url_history_db_path='url_history.db'):
        self.content_db_path = content_db_path
        self.url_manager = URLManager(url_history_db_path)
        self.global_queue = global_queue
        self.init_content_db()
        
        # Queue state tracking
        self.queue_state = {
            'total_urls': 0,
            'queued_urls': 0,
            'processing_urls': 0,
            'completed_urls': 0,
            'failed_urls': 0,
            'current_url': None,
            'current_depth': 0,
            'start_time': None,
            'estimated_completion': None,
            'errors': [],
            'stop_requested': False
        }

        # Reset queue state for new crawl
        self.reset_queue_state()
    
    def get_queue_state(self):
        """Get current queue state"""
        # Get global queue state
        global_state = self.global_queue.get_queue_state()
        if global_state:
            self.queue_state.update(global_state)
        
        state = self.queue_state.copy()
        return state
    
    def update_queue_state(self, **kwargs):
        """Update queue state"""
        for key, value in kwargs.items():
            if key in self.queue_state:
                self.queue_state[key] = value
    
    def reset_queue_state(self):
        """Reset queue state for new crawl"""
        self.queue_state.update({
            'total_urls': 0,
            'queued_urls': 0,
            'processing_urls': 0,
            'completed_urls': 0,
            'failed_urls': 0,
            'current_url': None,
            'current_depth': 0,
            'start_time': datetime.now(),
            'estimated_completion': None,
            'errors': [],
            'stop_requested': False
        })
    
    def init_content_db(self):
        """Initialize the content database"""
        conn = sqlite3.connect(self.content_db_path)
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS crawled_content (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                url TEXT NOT NULL UNIQUE,
                title TEXT,
                content TEXT,
                html_content TEXT,
                links TEXT,
                crawled_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                crawl_depth INTEGER DEFAULT 0
            )
        ''')
        conn.commit()
        conn.close()
    
    def save_content_to_db(self, url, title, content, html_content, links, depth=0):
        """Save crawled content to the content database"""
        conn = sqlite3.connect(self.content_db_path)
        cursor = conn.cursor()
        try:
            cursor.execute('''
                INSERT OR REPLACE INTO crawled_content (url, title, content, html_content, links, crawl_depth)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (url, title, content, html_content, '\n'.join(links), depth))
            conn.commit()
            return True
        except Exception as e:
            logger.error(f"Error saving to database: {e}")
            return False
        finally:
            conn.close()
    
    def url_exists_in_content_db(self, url):
        """Check if URL already exists in content database"""
        conn = sqlite3.connect(self.content_db_path)
        cursor = conn.cursor()
        cursor.execute('SELECT 1 FROM crawled_content WHERE url = ?', (url,))
        exists = cursor.fetchone() is not None
        conn.close()
        return exists
    
    def get_crawled_content_data(self):
        """Get all crawled content data"""
        conn = sqlite3.connect(self.content_db_path)
        cursor = conn.cursor()
        cursor.execute('''
            SELECT url, title, content, html_content, links, crawled_at, crawl_depth
            FROM crawled_content 
            ORDER BY crawled_at DESC
        ''')
        data = cursor.fetchall()
        conn.close()
        return data
    
    def get_html_content_by_url(self, url):
        """Get HTML content for a specific URL"""
        conn = sqlite3.connect(self.content_db_path)
        cursor = conn.cursor()
        cursor.execute('''
            SELECT html_content FROM crawled_content WHERE url = ?
        ''', (url,))
        result = cursor.fetchone()
        conn.close()
        return result[0] if result else None
    
    def clean_text(self, text):
        """Clean and extract meaningful text content"""
        if not text:
            return ""
        # Remove extra whitespace and newlines
        text = re.sub(r'\s+', ' ', text.strip())
        return text
    
    def extract_content(self, soup):
        """Extract main content from the webpage"""
        # Remove script and style elements
        for script in soup(["script", "style"]):
            script.decompose()
        
        # Get text content
        text = soup.get_text()
        text = self.clean_text(text)
        
        # Limit content length to avoid database issues
        if len(text) > 10000:
            text = text[:10000] + "... [truncated]"
        
        return text
    
    def is_same_domain(self, base_url, link_url):
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
    
    def normalize_url(self, url):
        """Normalize URL by removing fragments and query parameters"""
        try:
            parsed = urlparse(url)
            # Keep scheme, netloc, and path, but remove query and fragment
            normalized = f"{parsed.scheme}://{parsed.netloc}{parsed.path}"
            # Remove trailing slash for consistency
            if normalized.endswith('/') and len(normalized) > 1:
                normalized = normalized.rstrip('/')
            return normalized
        except Exception as e:
            logger.warning(f"Error normalizing URL {url}: {e}")
            return url
    
    def estimate_completion_time(self):
        """Estimate completion time based on current progress"""
        if self.queue_state['completed_urls'] == 0 or not self.queue_state['start_time']:
            return None
        
        elapsed = (datetime.now() - self.queue_state['start_time']).total_seconds()
        avg_time_per_url = elapsed / self.queue_state['completed_urls']
        remaining_urls = self.queue_state['queued_urls']
        estimated_remaining = remaining_urls * avg_time_per_url
        
        return datetime.now().timestamp() + estimated_remaining
    
    def extract_links(self, soup, current_url, base_url):
        """Extract and filter links from the page"""
        links = []
        discovered_urls = []
        
        try:
            for tag in soup.find_all('a', href=True):
                href = tag['href'].strip()
                if not href:
                    continue
                
                # Convert relative URLs to absolute
                try:
                    absolute_link = urljoin(current_url, href)
                except Exception as e:
                    logger.warning(f"Error joining URL {current_url} with {href}: {e}")
                    continue
                
                # Normalize the URL
                normalized_link = self.normalize_url(absolute_link)
                
                # Filter out unwanted links
                if (not absolute_link.startswith(('javascript:', 'mailto:', '#', 'tel:', 'ftp:')) and
                    not absolute_link.endswith(('.pdf', '.jpg', '.jpeg', '.png', '.gif', '.css', '.js')) and
                    self.is_same_domain(base_url, absolute_link)):
                    
                    links.append(absolute_link)
                    discovered_urls.append(normalized_link)
            
            logger.info(f"Found {len(links)} links on {current_url}")
            if links:
                logger.info(f"Sample links: {links[:3]}")
                
        except Exception as e:
            logger.error(f"Error extracting links from {current_url}: {e}")
        
        return links, discovered_urls
    
    def crawl_single_url(self, url, base_url):
        """Crawl a single URL"""
        normalized_url = self.normalize_url(url)
        
        # Check if stop is requested
        if self.queue_state['stop_requested']:
            return None
        
        # Update queue state
        self.update_queue_state(
            current_url=url,
            processing_urls=1
        )
        
        try:
            logger.info(f"Crawling: {url}")
            
            # Check if already in content database
            if self.url_exists_in_content_db(normalized_url):
                logger.info(f"Already crawled: {normalized_url}")
                return {'status': 'already_crawled', 'url': url}
            
            # Fetch the page with timing
            start_time = time.time()
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            response = requests.get(url, timeout=10, headers=headers)
            response_time = time.time() - start_time
            response.raise_for_status()
            
            # Get the raw HTML content
            html_content = response.text
            
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # Extract title
            title = soup.find('title')
            title_text = title.get_text() if title else "No title found"
            
            # Extract content
            content = self.extract_content(soup)
            
            # Extract and filter links
            links, discovered_urls = self.extract_links(soup, url, base_url)
            
            # Save to content database (including HTML)
            if self.save_content_to_db(normalized_url, title_text, content, html_content, links):
                logger.info(f"Saved: {normalized_url} - HTML size: {len(html_content)} chars")
            
            # Save to URL history database
            self.url_manager.add_url(
                url=normalized_url,
                status_code=response.status_code,
                response_time=response_time,
                content_length=len(response.content),
                metadata={
                    'title': title_text,
                    'links_count': len(links),
                    'content_length': len(content),
                    'html_length': len(html_content)
                }
            )
            
            return {
                'status': 'success',
                'url': url,
                'links_found': len(links),
                'content_length': len(content),
                'html_length': len(html_content),
                'discovered_urls': discovered_urls
            }
            
        except Exception as e:
            error_msg = f"Error crawling {url}: {str(e)}"
            logger.error(error_msg)
            
            # Update queue state
            self.queue_state['errors'].append(error_msg)
            self.queue_state['failed_urls'] += 1
            
            # Still record the failed attempt in URL history
            self.url_manager.add_url(
                url=normalized_url,
                status_code=None,
                response_time=None,
                content_length=None,
                metadata={'error': str(e)}
            )
            
            return {'status': 'error', 'url': url, 'error': str(e)}
        
        finally:
            # Update queue state
            self.update_queue_state(
                processing_urls=0,
                completed_urls=self.queue_state['completed_urls'] + 1,
                estimated_completion=self.estimate_completion_time()
            )
    
    def crawl_website(self, base_url):
        """Recursively crawl a website with unlimited depth and pages using global queue"""
        if not base_url.startswith(('http://', 'https://')):
            base_url = 'https://' + base_url
        # Add initial URL to global queue
        self.global_queue.add_url(base_url, priority=10)
        logger.info(f"Starting single-threaded crawl of {base_url} using global queue")
        crawled_count = 0
        while not self.queue_state['stop_requested']:
            # Get next URL from global queue
            queue_item = self.global_queue.get_next_url()
            if not queue_item:
                logger.info("No more URLs in global queue")
                break
            current_url = queue_item
            # Crawl the URL
            result = self.crawl_single_url(current_url, base_url)
            
            if result and result['status'] == 'success':
                crawled_count += 1
                logger.info(f"Completed: {current_url} - Found {result['links_found']} links")
                
                # Add discovered URLs to global queue
                for link in result.get('discovered_urls', []):
                    self.global_queue.add_url(link, priority=5)
                
                # Log progress periodically
                if crawled_count % 10 == 0:
                    queue_state = self.global_queue.get_queue_state()
                    if queue_state:
                        logger.info(f"Progress: {crawled_count} completed, "
                                  f"{queue_state['queued_urls']} queued, "
                                  f"{queue_state['total_urls']} total discovered")
                
                # Be respectful - add small delay between requests
                time.sleep(0.5)
            
            elif result and result['status'] == 'already_crawled':
                logger.info(f"Skipped (already crawled): {current_url}")
            
            elif result and result['status'] == 'error':
                logger.warning(f"Failed: {current_url} - {result.get('error', 'Unknown error')}")
        
        # Final queue state update
        self.update_queue_state(
            queued_urls=0,
            processing_urls=0
        )
        
        logger.info("Crawling completed")
        logger.info(f"Final stats: {crawled_count} completed, "
                   f"{self.queue_state['failed_urls']} failed, "
                   f"{self.queue_state['total_urls']} total URLs discovered")
        
        return {
            'total_visited': self.queue_state['total_urls'],
            'completed_urls': crawled_count,
            'failed_urls': self.queue_state['failed_urls'],
            'errors': self.queue_state['errors'],
            'queue_state': self.get_queue_state()
        }
    
    def stop_crawling(self):
        """Request to stop the current crawl"""
        self.update_queue_state(stop_requested=True)
        logger.info("Stop crawl requested")
    
    def get_url_history_stats(self):
        """Get URL history statistics"""
        return self.url_manager.get_database_stats()
    
    def get_recent_urls(self, hours=24, limit=20):
        """Get recently visited URLs"""
        return self.url_manager.get_recent_urls(hours, limit)
    
    def get_most_visited_urls(self, limit=10):
        """Get most frequently visited URLs"""
        return self.url_manager.get_most_visited_urls(limit)
    
    def get_url_info(self, url):
        """Get information about a specific URL"""
        return self.url_manager.get_url_info(url)
    
    def is_recently_visited(self, url, hours=24):
        """Check if URL was visited within specified hours"""
        return self.url_manager.is_recently_visited(url, hours)
    
    def get_global_queue_state(self):
        """Get global queue state"""
        return self.global_queue.get_queue_state()
    
    def clear_global_queue(self):
        """Clear global queue"""
        return self.global_queue.clear_queue()
    
    def get_pending_urls(self, base_url=None, limit=100):
        """Get pending URLs from global queue"""
        # For now, return a simple list since the global queue doesn't store URLs persistently
        # In a real implementation, this would query the database
        return [] 