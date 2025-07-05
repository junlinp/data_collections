"""
Memory Optimization Module for Web Crawler
Provides utilities to reduce memory usage and prevent memory leaks
"""

import gc
import sys
import psutil
import logging
from functools import wraps
from contextlib import contextmanager
import weakref
from bs4 import BeautifulSoup
import json

logger = logging.getLogger(__name__)

class MemoryOptimizer:
    """Memory optimization utilities for crawler service"""
    
    def __init__(self):
        self.memory_threshold = 3000  # MB
        self.cleanup_interval = 100   # Process every N URLs
        self.process_count = 0
        
    def monitor_memory(self, func):
        """Decorator to monitor memory usage of functions"""
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Get memory before
            process = psutil.Process()
            memory_before = process.memory_info().rss / 1024 / 1024
            
            try:
                result = func(*args, **kwargs)
                
                # Check memory after
                memory_after = process.memory_info().rss / 1024 / 1024
                memory_diff = memory_after - memory_before
                
                if memory_diff > 50:  # Log if increased by more than 50MB
                    logger.warning(f"Memory increased by {memory_diff:.1f}MB in {func.__name__}")
                
                # Force cleanup if memory is high
                if memory_after > self.memory_threshold:
                    logger.warning(f"High memory usage: {memory_after:.1f}MB - forcing cleanup")
                    self.force_cleanup()
                
                return result
                
            except Exception as e:
                # Cleanup on error
                self.force_cleanup()
                raise e
                
        return wrapper
    
    def force_cleanup(self):
        """Force garbage collection and cleanup"""
        try:
            # Force garbage collection
            collected = gc.collect()
            logger.info(f"Garbage collection: {collected} objects collected")
            
            # Get current memory usage
            process = psutil.Process()
            memory_after = process.memory_info().rss / 1024 / 1024
            logger.info(f"Memory after cleanup: {memory_after:.1f}MB")
            
        except Exception as e:
            logger.error(f"Error during cleanup: {e}")
    
    @contextmanager
    def memory_managed_processing(self, operation_name="operation"):
        """Context manager for memory-managed processing"""
        process = psutil.Process()
        memory_before = process.memory_info().rss / 1024 / 1024
        
        try:
            yield
        finally:
            # Cleanup after processing
            memory_after = process.memory_info().rss / 1024 / 1024
            memory_diff = memory_after - memory_before
            
            if memory_diff > 100:  # If increased by more than 100MB
                logger.warning(f"High memory usage in {operation_name}: {memory_diff:.1f}MB increase")
                self.force_cleanup()
            
            self.process_count += 1
            if self.process_count % self.cleanup_interval == 0:
                logger.info(f"Periodic cleanup after {self.process_count} operations")
                self.force_cleanup()

class OptimizedHTMLProcessor:
    """Memory-optimized HTML processing utilities"""
    
    def __init__(self, max_html_size=500000):  # 500KB max HTML
        self.max_html_size = max_html_size
        
    def process_html_efficiently(self, html_content, url):
        """Process HTML content with memory optimization"""
        try:
            # Truncate large HTML to prevent memory issues
            if len(html_content) > self.max_html_size:
                logger.warning(f"Truncating large HTML for {url}: {len(html_content)} -> {self.max_html_size} chars")
                html_content = html_content[:self.max_html_size] + "..."
            
            # Use memory-efficient parsing
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # Extract data efficiently
            title = self._extract_title_efficiently(soup)
            content = self._extract_content_efficiently(soup)
            links = self._extract_links_efficiently(soup, url)
            
            # Clear soup object immediately
            soup.clear()
            del soup
            
            return {
                'title': title,
                'content': content,
                'links': links,
                'content_length': len(content) if content else 0
            }
            
        except Exception as e:
            logger.error(f"Error in efficient HTML processing: {e}")
            return None
    
    def _extract_title_efficiently(self, soup):
        """Extract title with minimal memory usage"""
        try:
            title_tag = soup.find('title')
            if title_tag:
                title = title_tag.get_text(strip=True)
                title_tag.clear()  # Clear the tag
                return title[:200]  # Limit title length
            return None
        except Exception as e:
            logger.error(f"Error extracting title: {e}")
            return None
    
    def _extract_content_efficiently(self, soup):
        """Extract content with memory optimization"""
        try:
            # Remove memory-heavy elements first
            for tag in soup(["script", "style", "nav", "header", "footer", "aside", "form", "iframe"]):
                tag.decompose()
            
            # Extract text in chunks to avoid large string operations
            text_parts = []
            for element in soup.find_all(text=True):
                text = element.strip()
                if text and len(text) > 10:  # Only keep meaningful text
                    text_parts.append(text)
            
            # Join efficiently
            content = ' '.join(text_parts)
            
            # Limit content size
            if len(content) > 10000:  # 10KB max content
                content = content[:10000] + "..."
            
            return content
            
        except Exception as e:
            logger.error(f"Error extracting content: {e}")
            return None
    
    def _extract_links_efficiently(self, soup, base_url):
        """Extract links with memory optimization"""
        try:
            links = []
            for link in soup.find_all('a', href=True):
                href = link.get('href')
                if href and self._is_valid_link(href, base_url):
                    links.append(href)
                    if len(links) >= 50:  # Limit links per page
                        break
                link.clear()  # Clear the link element
            
            return links[:50]  # Limit to 50 links max
            
        except Exception as e:
            logger.error(f"Error extracting links: {e}")
            return []
    
    def _is_valid_link(self, href, base_url):
        """Check if link is valid and should be processed"""
        try:
            # Skip non-HTTP links
            if not href.startswith(('http://', 'https://', '/')):
                return False
            
            # Skip common file extensions that are not HTML
            skip_extensions = ['.jpg', '.jpeg', '.png', '.gif', '.pdf', '.doc', '.zip', '.exe', '.mp4', '.mp3']
            if any(href.lower().endswith(ext) for ext in skip_extensions):
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"Error validating link: {e}")
            return False

class MemoryEfficientDataStore:
    """Memory-efficient data storage utilities"""
    
    def __init__(self, max_items=1000):
        self.max_items = max_items
        self.data = {}
        self.access_order = []
    
    def store_with_limit(self, key, value):
        """Store data with automatic cleanup of old items"""
        try:
            # Remove old item if exists
            if key in self.data:
                self.access_order.remove(key)
            
            # Add new item
            self.data[key] = value
            self.access_order.append(key)
            
            # Cleanup if too many items
            if len(self.data) > self.max_items:
                # Remove oldest items
                items_to_remove = len(self.data) - self.max_items
                for _ in range(items_to_remove):
                    if self.access_order:
                        old_key = self.access_order.pop(0)
                        if old_key in self.data:
                            del self.data[old_key]
            
        except Exception as e:
            logger.error(f"Error storing data: {e}")
    
    def get_memory_usage(self):
        """Get approximate memory usage of stored data"""
        try:
            total_size = 0
            for key, value in self.data.items():
                total_size += sys.getsizeof(key)
                total_size += sys.getsizeof(value)
            return total_size / 1024 / 1024  # MB
        except Exception as e:
            logger.error(f"Error calculating memory usage: {e}")
            return 0

# Global instances
memory_optimizer = MemoryOptimizer()
html_processor = OptimizedHTMLProcessor()
data_store = MemoryEfficientDataStore()

# Utility functions
def log_memory_usage(operation_name):
    """Log current memory usage"""
    try:
        process = psutil.Process()
        memory_mb = process.memory_info().rss / 1024 / 1024
        logger.info(f"Memory usage after {operation_name}: {memory_mb:.1f}MB")
        return memory_mb
    except Exception as e:
        logger.error(f"Error logging memory usage: {e}")
        return 0

def is_memory_critical():
    """Check if memory usage is critical"""
    try:
        process = psutil.Process()
        memory_mb = process.memory_info().rss / 1024 / 1024
        return memory_mb > 3000  # 3GB threshold
    except Exception as e:
        logger.error(f"Error checking memory: {e}")
        return False 