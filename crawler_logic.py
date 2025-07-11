"""
Main crawling logic for the web crawler
Separated from the web interface for better maintainability
"""

import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
from datetime import datetime
import re
import time
from collections import deque
from url_manager import URLManager
import logging
import json
import threading
import random
from redis_queue_manager import RedisQueueManager
from mongo_utils import get_mongo_manager

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class WebCrawler:
    def __init__(self):
        # Initialize MongoDB manager
        self.mongo_manager = get_mongo_manager()
        self.url_manager = URLManager()  # URLManager will be updated to use MongoDB
        self.global_queue = RedisQueueManager(host='redis', port=6379)
        
        # Create a session for better cookie handling and authenticity
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
        """Initialize the MongoDB connection"""
        # MongoDB connection is already initialized in constructor
        pass
    
    def save_content_to_db(self, url, title, content, html_content, links):
        """Save crawled content to MongoDB"""
        try:
            # Convert links to string if it's a list
            links_str = '\n'.join(links) if isinstance(links, list) else str(links)
            
            success = self.mongo_manager.save_web_content(
                url=url,
                title=title or '',
                html_content=html_content or '',
                text_content=content or ''
            )
            return success
        except Exception as e:
            logger.error(f"Error saving to MongoDB: {e}")
            return False
    
    def url_exists_in_content_db(self, url):
        """Check if URL already exists in MongoDB"""
        try:
            content = self.mongo_manager.get_web_content(url)
            return content is not None
        except Exception as e:
            logger.error(f"Error checking URL existence in MongoDB: {e}")
            return False
    
    def get_crawled_content_data(self, limit=None, offset=0):
        """Get crawled content data with pagination support from MongoDB"""
        try:
            # Get data from MongoDB
            docs = self.mongo_manager.get_all_web_content(limit=limit, skip=offset)
            
            # Convert to the expected format
            data = []
            for doc in docs:
                data.append((
                    doc.get('url', ''),
                    doc.get('title', ''),
                    doc.get('text_content', ''),
                    doc.get('links', ''),
                    doc.get('created_at', '')
                ))
            
            return data
        except Exception as e:
            logger.error(f"Error getting crawled content data from MongoDB: {e}")
            return []
    
    def get_crawled_content_with_html(self, limit=None, offset=0):
        """Get crawled content data with html_content from MongoDB (use sparingly due to memory usage)"""
        try:
            # Get data from MongoDB
            docs = self.mongo_manager.get_all_web_content(limit=limit, skip=offset)
            
            # Convert to the expected format
            data = []
            for doc in docs:
                data.append((
                    doc.get('url', ''),
                    doc.get('title', ''),
                    doc.get('text_content', ''),
                    doc.get('html_content', ''),
                    doc.get('links', ''),
                    doc.get('created_at', '')
                ))
            
            return data
        except Exception as e:
            logger.error(f"Error getting crawled content with HTML from MongoDB: {e}")
            return []
    
    def get_crawled_content_count(self):
        """Get total count of crawled content records from MongoDB"""
        try:
            return self.mongo_manager.count_web_content()
        except Exception as e:
            logger.error(f"Error getting crawled content count from MongoDB: {e}")
            return 0
    
    def get_html_content_by_url(self, url):
        """Get HTML content for a specific URL from MongoDB"""
        try:
            content = self.mongo_manager.get_web_content(url)
            return content.get('html_content') if content else None
        except Exception as e:
            logger.error(f"Error getting HTML content from MongoDB: {e}")
            return None
    
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
                # Filter links - allow all links from the same domain as base_url
                if (not absolute_link.startswith(('javascript:', 'mailto:', '#', 'tel:', 'ftp:')) and
                    not absolute_link.endswith(('.pdf', '.jpg', '.jpeg', '.png', '.gif', '.css', '.js', '.xml', '.zip', '.exe')) and
                    self.is_same_domain(base_url, absolute_link)):
                    links.append(absolute_link)
                    discovered_urls.append(normalized_link)
            logger.info(f"[DEBUG] All <a href> found on {current_url}: {all_found}")
            logger.info(f"Found {len(links)} links on {current_url}")
            if links:
                logger.info(f"Sample links: {links[:3]}")
        except Exception as e:
            logger.error(f"Error extracting links from {current_url}: {e}")
        return links, discovered_urls
    
    def get_random_user_agent(self):
        user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Safari/605.1.15',
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:124.0) Gecko/20100101 Firefox/124.0',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7; rv:124.0) Gecko/20100101 Firefox/124.0',
        ]
        return random.choice(user_agents)

    def get_random_referer(self, base_url):
        referers = [
            'https://www.google.com/',
            'https://www.bing.com/',
            'https://duckduckgo.com/',
            base_url,
        ]
        return random.choice(referers)

    def establish_session(self, base_url):
        """Establish a session with the target website to get cookies and appear more authentic"""
        try:
            parsed_url = urlparse(base_url)
            if parsed_url.netloc:
                main_domain = f"https://{parsed_url.netloc}"
                logger.info(f"Establishing session with {main_domain}")
                self.session.cookies.clear()
                self.session.headers['User-Agent'] = self.get_random_user_agent()
                self.session.headers['Referer'] = self.get_random_referer(main_domain)
                try:
                    robots_url = f"{main_domain}/robots.txt"
                    self.session.get(robots_url, timeout=5)
                    time.sleep(random.uniform(0.5, 1.5))
                except:
                    pass
                response = self.session.get(main_domain, timeout=15, allow_redirects=True)
                if response.status_code == 200:
                    logger.info(f"Successfully established session with {main_domain}")
                    try:
                        common_paths = ['/', '/index.html', '/home']
                        for path in common_paths[:1]:
                            try:
                                test_url = f"{main_domain}{path}"
                                if test_url != main_domain:
                                    self.session.get(test_url, timeout=10)
                                    time.sleep(random.uniform(1, 2))
                                    break
                            except:
                                pass
                    except:
                        pass
                    time.sleep(random.uniform(1, 2))
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
                response = self.session.get(url, timeout=60, allow_redirects=True, headers=headers)
            else:
                response = self.session.get(url, timeout=20, allow_redirects=True)
            response_time = time.time() - start_time
            
            # Check for common anti-bot responses
            if response.status_code == 403:
                logger.warning(f"403 Forbidden - likely blocked by anti-bot protection for {url}")
                # Try with different headers
                self.session.headers['User-Agent'] = self.get_random_user_agent()
                time.sleep(2)
                # Use longer timeout for retry
                response = self.session.get(url, timeout=60, allow_redirects=True)
            
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
        self.global_queue.add_url(base_url)
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
                    self.global_queue.add_url(link)
                
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