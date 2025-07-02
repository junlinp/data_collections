"""
Queue Manager - Handles URL queuing and worker coordination
Implements a queue system where URLs can be visited if not visited in the last 24 hours
"""

import sqlite3
import threading
import time
import json
from datetime import datetime, timedelta
from collections import deque
from urllib.parse import urlparse
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class QueueManager:
    """Manages URL queue with 24-hour visit tracking"""
    
    def __init__(self, db_path='queue_manager.db'):
        self.db_path = db_path
        self.lock = threading.Lock()
        self.queue = deque()
        self.processing_urls = set()
        self.workers = {}
        self.init_db()
    
    def init_db(self):
        """Initialize the queue database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Create queue table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS url_queue (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                url TEXT NOT NULL UNIQUE,
                domain TEXT NOT NULL,
                priority INTEGER DEFAULT 0,
                added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                scheduled_for TIMESTAMP,
                status TEXT DEFAULT 'pending',
                processing_started TIMESTAMP,
                completed_at TIMESTAMP,
                error_message TEXT
            )
        ''')
        
        # Create visit history table for 24-hour tracking
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS visit_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                url TEXT NOT NULL,
                visited_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                status_code INTEGER,
                response_time REAL,
                content_length INTEGER
            )
        ''')
        
        # Create indexes
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_url_queue_url ON url_queue(url)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_url_queue_status ON url_queue(status)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_url_queue_scheduled ON url_queue(scheduled_for)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_visit_history_url ON visit_history(url)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_visit_history_visited_at ON visit_history(visited_at)')
        
        conn.commit()
        conn.close()
    
    def add_url_to_queue(self, url, priority=0):
        """Add URL to queue if not visited in last 24 hours"""
        with self.lock:
            # Check if URL was visited in last 24 hours
            if self.is_recently_visited(url, hours=24):
                logger.info(f"URL {url} was visited recently, skipping")
                return False, "URL was visited in the last 24 hours"
            
            # Check if URL is already in queue
            if self.is_url_in_queue(url):
                logger.info(f"URL {url} is already in queue")
                return False, "URL is already in queue"
            
            domain = self.extract_domain(url)
            
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            try:
                cursor.execute('''
                    INSERT INTO url_queue (url, domain, priority, status)
                    VALUES (?, ?, ?, 'pending')
                ''', (url, domain, priority))
                
                conn.commit()
                
                # Add to in-memory queue
                self.queue.append((url, priority))
                
                logger.info(f"Added URL to queue: {url}")
                return True, "URL added to queue successfully"
                
            except sqlite3.IntegrityError:
                return False, "URL already exists in queue"
            except Exception as e:
                logger.error(f"Error adding URL to queue: {e}")
                return False, f"Error adding URL to queue: {str(e)}"
            finally:
                conn.close()
    
    def get_next_url_for_worker(self, worker_id):
        """Get next URL from queue for a worker"""
        with self.lock:
            if not self.queue:
                return None
            
            # Get URL with highest priority
            url, priority = self.queue.popleft()
            
            # Mark as processing
            self.processing_urls.add(url)
            
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            try:
                cursor.execute('''
                    UPDATE url_queue 
                    SET status = 'processing', 
                        processing_started = ?
                    WHERE url = ?
                ''', (datetime.now(), url))
                
                conn.commit()
                
                logger.info(f"Assigned URL {url} to worker {worker_id}")
                return url
                
            except Exception as e:
                logger.error(f"Error assigning URL to worker: {e}")
                # Put URL back in queue
                self.queue.appendleft((url, priority))
                self.processing_urls.discard(url)
                return None
            finally:
                conn.close()
    
    def mark_url_completed(self, url, status_code=None, response_time=None, content_length=None):
        """Mark URL as completed and record visit"""
        with self.lock:
            self.processing_urls.discard(url)
            
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            try:
                # Update queue status
                cursor.execute('''
                    UPDATE url_queue 
                    SET status = 'completed', 
                        completed_at = ?
                    WHERE url = ?
                ''', (datetime.now(), url))
                
                # Record visit in history
                cursor.execute('''
                    INSERT INTO visit_history (url, status_code, response_time, content_length)
                    VALUES (?, ?, ?, ?)
                ''', (url, status_code, response_time, content_length))
                
                conn.commit()
                
                logger.info(f"Marked URL as completed: {url}")
                
            except Exception as e:
                logger.error(f"Error marking URL as completed: {e}")
            finally:
                conn.close()
    
    def mark_url_failed(self, url, error_message):
        """Mark URL as failed"""
        with self.lock:
            self.processing_urls.discard(url)
            
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            try:
                cursor.execute('''
                    UPDATE url_queue 
                    SET status = 'failed', 
                        error_message = ?
                    WHERE url = ?
                ''', (error_message, url))
                
                conn.commit()
                
                logger.info(f"Marked URL as failed: {url} - {error_message}")
                
            except Exception as e:
                logger.error(f"Error marking URL as failed: {e}")
            finally:
                conn.close()
    
    def is_recently_visited(self, url, hours=24):
        """Check if URL was visited within specified hours"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        threshold = datetime.now() - timedelta(hours=hours)
        
        cursor.execute('''
            SELECT COUNT(*) FROM visit_history 
            WHERE url = ? AND visited_at > ?
        ''', (url, threshold))
        
        count = cursor.fetchone()[0]
        conn.close()
        
        return count > 0
    
    def is_url_in_queue(self, url):
        """Check if URL is already in queue"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT COUNT(*) FROM url_queue 
            WHERE url = ? AND status IN ('pending', 'processing')
        ''', (url,))
        
        count = cursor.fetchone()[0]
        conn.close()
        
        return count > 0
    
    def get_queue_stats(self):
        """Get current queue statistics"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            # Get counts by status
            cursor.execute('''
                SELECT status, COUNT(*) 
                FROM url_queue 
                GROUP BY status
            ''')
            
            status_counts = dict(cursor.fetchall())
            
            # Get total counts
            cursor.execute('SELECT COUNT(*) FROM url_queue')
            total_urls = cursor.fetchone()[0]
            
            cursor.execute('SELECT COUNT(*) FROM visit_history')
            total_visits = cursor.fetchone()[0]
            
            return {
                'total_urls': total_urls,
                'total_visits': total_visits,
                'pending_urls': status_counts.get('pending', 0),
                'processing_urls': status_counts.get('processing', 0),
                'completed_urls': status_counts.get('completed', 0),
                'failed_urls': status_counts.get('failed', 0),
                'in_memory_queue': len(self.queue),
                'currently_processing': len(self.processing_urls)
            }
            
        except Exception as e:
            logger.error(f"Error getting queue stats: {e}")
            return {}
        finally:
            conn.close()
    
    def get_pending_urls(self, limit=100):
        """Get list of pending URLs"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT url, domain, priority, added_at 
            FROM url_queue 
            WHERE status = 'pending'
            ORDER BY priority DESC, added_at ASC
            LIMIT ?
        ''', (limit,))
        
        urls = []
        for row in cursor.fetchall():
            urls.append({
                'url': row[0],
                'domain': row[1],
                'priority': row[2],
                'added_at': row[3]
            })
        
        conn.close()
        return urls
    
    def clear_queue(self):
        """Clear all pending URLs from queue"""
        with self.lock:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            try:
                cursor.execute('DELETE FROM url_queue WHERE status = "pending"')
                conn.commit()
                
                # Clear in-memory queue
                self.queue.clear()
                
                logger.info("Queue cleared")
                
            except Exception as e:
                logger.error(f"Error clearing queue: {e}")
            finally:
                conn.close()
    
    def extract_domain(self, url):
        """Extract domain from URL"""
        try:
            parsed = urlparse(url)
            return parsed.netloc
        except:
            return "unknown"
    
    def cleanup_old_records(self, days=7):
        """Clean up old completed/failed records"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        threshold = datetime.now() - timedelta(days=days)
        
        try:
            cursor.execute('''
                DELETE FROM url_queue 
                WHERE status IN ('completed', 'failed') 
                AND completed_at < ?
            ''', (threshold,))
            
            conn.commit()
            
            logger.info(f"Cleaned up old queue records older than {days} days")
            
        except Exception as e:
            logger.error(f"Error cleaning up old records: {e}")
        finally:
            conn.close()

# Global queue manager instance
queue_manager = QueueManager() 