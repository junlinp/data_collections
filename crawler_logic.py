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
        self.completed_urls = 0
        self.failed_urls = 0
    
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
    
    def mark_completed(self):
        """Mark a URL as completed"""
        with self.lock:
            self.completed_urls += 1
    
    def mark_failed(self):
        """Mark a URL as failed"""
        with self.lock:
            self.failed_urls += 1
                    
    def get_queue_state(self):
        """Get current queue state"""
        with self.lock:
            return {
                'total_urls': len(self.queue) + self.completed_urls + self.failed_urls,
                'queued_urls': len(self.queue),
                'processing_urls': 0,
                'completed_urls': self.completed_urls,
                'failed_urls': self.failed_urls
            }
                
    def clear_queue(self):
        """Clear queue"""
        with self.lock:
            self.queue = deque()
            self.queue_urls = set()
            self.completed_urls = 0
            self.failed_urls = 0
                
 
# Global queue instance
global_queue = GlobalQueue()

class WebCrawler:
    def __init__(self, content_db_path='web_crawler.db', url_history_db_path='url_history.db'):
        self.content_db_path = content_db_path
        self.url_manager = URLManager(url_history_db_path)
        self.global_queue = global_queue
        
        # Create a session for better cookie handling and authenticity
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
            'X-Requested-With': 'XMLHttpRequest',
        })
        
        # Add more realistic browser behavior
        self.session.verify = True
        self.session.allow_redirects = True
        
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
        
        # Create a copy of current state
        state = self.queue_state.copy()
        
        # Update only the queue-related fields from global state
        if global_state:
            state.update({
                'total_urls': global_state.get('total_urls', 0),
                'queued_urls': global_state.get('queued_urls', 0),
                'processing_urls': global_state.get('processing_urls', 0),
                'completed_urls': global_state.get('completed_urls', 0),
                'failed_urls': global_state.get('failed_urls', 0)
            })
        
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
        all_found = []
        try:
            for tag in soup.find_all('a', href=True):
                href = tag['href'].strip()
                if not href:
                    continue
                all_found.append(href)
                # Convert relative URLs to absolute
                try:
                    absolute_link = urljoin(current_url, href)
                except Exception as e:
                    logger.warning(f"Error joining URL {current_url} with {href}: {e}")
                    continue
                # Normalize the URL
                normalized_link = self.normalize_url(absolute_link)
                # Relaxed filter: allow all links that are internal to CNN
                if (not absolute_link.startswith(('javascript:', 'mailto:', '#', 'tel:', 'ftp:')) and
                    not absolute_link.endswith(('.pdf', '.jpg', '.jpeg', '.png', '.gif', '.css', '.js')) and
                    (absolute_link.startswith('https://edition.cnn.com') or absolute_link.startswith('/'))):
                    links.append(absolute_link)
                    discovered_urls.append(normalized_link)
            logger.info(f"[DEBUG] All <a href> found on {current_url}: {all_found}")
            logger.info(f"Found {len(links)} links on {current_url}")
            if links:
                logger.info(f"Sample links: {links[:3]}")
        except Exception as e:
            logger.error(f"Error extracting links from {current_url}: {e}")
        return links, discovered_urls
    
    def establish_session(self, base_url):
        """Establish a session with the target website to get cookies and appear more authentic"""
        try:
            parsed_url = urlparse(base_url)
            if parsed_url.netloc:
                # First visit the main domain to establish session
                main_domain = f"https://{parsed_url.netloc}"
                logger.info(f"Establishing session with {main_domain}")
                
                # Clear any existing cookies for this domain
                self.session.cookies.clear()
                
                # Add a more realistic referer
                self.session.headers['Referer'] = 'https://www.google.com/'
                
                # First, try to visit the robots.txt to appear more like a real browser
                try:
                    robots_url = f"{main_domain}/robots.txt"
                    self.session.get(robots_url, timeout=5)
                    time.sleep(0.5)
                except:
                    pass  # Ignore robots.txt errors
                
                # Visit the main page first with a more realistic approach
                response = self.session.get(main_domain, timeout=15, allow_redirects=True)
                
                if response.status_code == 200:
                    logger.info(f"Successfully established session with {main_domain}")
                    
                    # Try to visit a few more pages to establish a browsing pattern
                    try:
                        # Visit common pages to establish session
                        common_paths = ['/', '/index.html', '/home']
                        for path in common_paths[:1]:  # Just visit one to avoid being too aggressive
                            try:
                                test_url = f"{main_domain}{path}"
                                if test_url != main_domain:  # Avoid duplicate requests
                                    self.session.get(test_url, timeout=10)
                                    time.sleep(1)
                                    break
                            except:
                                pass
                    except:
                        pass
                    
                    # Small delay after establishing session
                    time.sleep(2)
                    return True
                else:
                    logger.warning(f"Failed to establish session with {main_domain}: {response.status_code}")
                    return False
        except Exception as e:
            logger.warning(f"Error establishing session: {e}")
            return False
    
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
            
            # Add referer for better authenticity
            parsed_url = urlparse(url)
            if parsed_url.netloc:
                # Use a more realistic referer pattern
                if base_url and base_url != url:
                    self.session.headers['Referer'] = base_url
                else:
                    self.session.headers['Referer'] = f'https://{parsed_url.netloc}/'
            
            # Add a more realistic delay pattern
            delay = 1.0 + (time.time() % 2) * 1.5  # 1-2.5 seconds
            time.sleep(delay)
            
            # Add some request headers that change slightly to appear more human
            self.session.headers['Accept'] = 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7'
            
            response = self.session.get(url, timeout=20, allow_redirects=True)
            response_time = time.time() - start_time
            
            # Check for common anti-bot responses
            if response.status_code == 403:
                logger.warning(f"403 Forbidden - likely blocked by anti-bot protection for {url}")
                # Try with different headers
                self.session.headers['User-Agent'] = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36'
                time.sleep(2)
                response = self.session.get(url, timeout=20, allow_redirects=True)
            
            response.raise_for_status()
            
            # Get the raw HTML content
            html_content = response.text
            
            # Debug: Log response details
            logger.info(f"[DEBUG] Response status: {response.status_code}")
            logger.info(f"[DEBUG] Response headers: {dict(response.headers)}")
            logger.info(f"[DEBUG] Content length: {len(html_content)}")
            logger.info(f"[DEBUG] First 500 chars: {html_content[:500]}")
            
            # Check if we got a real page or a bot detection page
            if len(html_content) < 1000 or 'access denied' in html_content.lower() or 'blocked' in html_content.lower():
                logger.warning(f"Possible bot detection page for {url} - content length: {len(html_content)}")
            
            # Check if content looks like HTML
            if not html_content.strip().startswith('<'):
                logger.warning(f"Content doesn't look like HTML for {url} - starts with: {html_content[:100]}")
            
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
            
            # Mark as failed in global queue
            self.global_queue.mark_failed()
            
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
            
            # Mark as completed in global queue
            self.global_queue.mark_completed()
    
    def crawl_website(self, base_url):
        """Recursively crawl a website with unlimited depth and pages using global queue"""
        if not base_url.startswith(('http://', 'https://')):
            base_url = 'https://' + base_url
            
        # Establish session with the target website
        self.establish_session(base_url)
        
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