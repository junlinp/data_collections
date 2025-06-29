import sqlite3
from datetime import datetime, timedelta
from urllib.parse import urlparse
import json

class URLManager:
    def __init__(self, db_path='url_history.db'):
        self.db_path = db_path
        self.init_db()
    
    def init_db(self):
        """Initialize the URL history database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Create URL history table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS url_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                url TEXT NOT NULL,
                domain TEXT NOT NULL,
                first_visited TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_visited TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                visit_count INTEGER DEFAULT 1,
                crawl_depth INTEGER DEFAULT 0,
                status_code INTEGER,
                response_time REAL,
                content_length INTEGER,
                metadata TEXT
            )
        ''')
        
        # Create index for faster lookups
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_url_history_url 
            ON url_history(url)
        ''')
        
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_url_history_domain 
            ON url_history(domain)
        ''')
        
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_url_history_last_visited 
            ON url_history(last_visited)
        ''')
        
        conn.commit()
        conn.close()
    
    def add_url(self, url, crawl_depth=0, status_code=None, response_time=None, 
                content_length=None, metadata=None):
        """Add or update a URL in the history"""
        domain = self.extract_domain(url)
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            # Check if URL already exists
            cursor.execute('''
                SELECT id, visit_count, first_visited 
                FROM url_history 
                WHERE url = ?
            ''', (url,))
            
            existing = cursor.fetchone()
            
            if existing:
                # Update existing record
                url_id, current_count, first_visited = existing
                cursor.execute('''
                    UPDATE url_history 
                    SET last_visited = ?, 
                        visit_count = ?, 
                        crawl_depth = ?,
                        status_code = ?,
                        response_time = ?,
                        content_length = ?,
                        metadata = ?
                    WHERE id = ?
                ''', (
                    datetime.now(),
                    current_count + 1,
                    crawl_depth,
                    status_code,
                    response_time,
                    content_length,
                    json.dumps(metadata) if metadata else None,
                    url_id
                ))
            else:
                # Insert new record
                cursor.execute('''
                    INSERT INTO url_history 
                    (url, domain, crawl_depth, status_code, response_time, content_length, metadata)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (
                    url,
                    domain,
                    crawl_depth,
                    status_code,
                    response_time,
                    content_length,
                    json.dumps(metadata) if metadata else None
                ))
            
            conn.commit()
            return True
            
        except Exception as e:
            print(f"Error adding URL to history: {e}")
            return False
        finally:
            conn.close()
    
    def get_url_info(self, url):
        """Get information about a specific URL"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT url, domain, first_visited, last_visited, visit_count, 
                   crawl_depth, status_code, response_time, content_length, metadata
            FROM url_history 
            WHERE url = ?
        ''', (url,))
        
        row = cursor.fetchone()
        conn.close()
        
        if row:
            return {
                'url': row[0],
                'domain': row[1],
                'first_visited': row[2],
                'last_visited': row[3],
                'visit_count': row[4],
                'crawl_depth': row[5],
                'status_code': row[6],
                'response_time': row[7],
                'content_length': row[8],
                'metadata': json.loads(row[9]) if row[9] else None
            }
        return None
    
    def is_recently_visited(self, url, hours=24):
        """Check if URL was visited within specified hours"""
        url_info = self.get_url_info(url)
        if not url_info:
            return False
        
        last_visited = datetime.fromisoformat(url_info['last_visited'])
        threshold = datetime.now() - timedelta(hours=hours)
        return last_visited > threshold
    
    def get_domain_stats(self, domain):
        """Get statistics for a specific domain"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT COUNT(*) as total_urls,
                   SUM(visit_count) as total_visits,
                   AVG(response_time) as avg_response_time,
                   MIN(first_visited) as first_crawl,
                   MAX(last_visited) as last_crawl
            FROM url_history 
            WHERE domain = ?
        ''', (domain,))
        
        row = cursor.fetchone()
        conn.close()
        
        if row and row[0] > 0:
            return {
                'domain': domain,
                'total_urls': row[0],
                'total_visits': row[1],
                'avg_response_time': row[2],
                'first_crawl': row[3],
                'last_crawl': row[4]
            }
        return None
    
    def get_recent_urls(self, hours=24, limit=100):
        """Get recently visited URLs"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        threshold = datetime.now() - timedelta(hours=hours)
        
        cursor.execute('''
            SELECT url, domain, last_visited, visit_count, crawl_depth
            FROM url_history 
            WHERE last_visited > ?
            ORDER BY last_visited DESC
            LIMIT ?
        ''', (threshold, limit))
        
        rows = cursor.fetchall()
        conn.close()
        
        return [
            {
                'url': row[0],
                'domain': row[1],
                'last_visited': row[2],
                'visit_count': row[3],
                'crawl_depth': row[4]
            }
            for row in rows
        ]
    
    def get_most_visited_urls(self, limit=20):
        """Get most frequently visited URLs"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT url, domain, visit_count, last_visited
            FROM url_history 
            ORDER BY visit_count DESC
            LIMIT ?
        ''', (limit,))
        
        rows = cursor.fetchall()
        conn.close()
        
        return [
            {
                'url': row[0],
                'domain': row[1],
                'visit_count': row[2],
                'last_visited': row[3]
            }
            for row in rows
        ]
    
    def cleanup_old_records(self, days=30):
        """Remove records older than specified days"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        threshold = datetime.now() - timedelta(days=days)
        
        cursor.execute('''
            DELETE FROM url_history 
            WHERE last_visited < ?
        ''', (threshold,))
        
        deleted_count = cursor.rowcount
        conn.commit()
        conn.close()
        
        return deleted_count
    
    def get_database_stats(self):
        """Get overall database statistics"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT COUNT(*) as total_urls,
                   COUNT(DISTINCT domain) as total_domains,
                   SUM(visit_count) as total_visits,
                   AVG(response_time) as avg_response_time,
                   MIN(first_visited) as earliest_visit,
                   MAX(last_visited) as latest_visit
            FROM url_history
        ''')
        
        row = cursor.fetchone()
        conn.close()
        
        if row:
            return {
                'total_urls': row[0],
                'total_domains': row[1],
                'total_visits': row[2],
                'avg_response_time': row[3],
                'earliest_visit': row[4],
                'latest_visit': row[5]
            }
        return None
    
    def extract_domain(self, url):
        """Extract domain from URL"""
        try:
            parsed = urlparse(url)
            return parsed.netloc
        except:
            return "unknown"
    
    def export_to_json(self, filename='url_history_export.json'):
        """Export URL history to JSON file"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT url, domain, first_visited, last_visited, visit_count, 
                   crawl_depth, status_code, response_time, content_length, metadata
            FROM url_history 
            ORDER BY last_visited DESC
        ''')
        
        rows = cursor.fetchall()
        conn.close()
        
        data = []
        for row in rows:
            data.append({
                'url': row[0],
                'domain': row[1],
                'first_visited': row[2],
                'last_visited': row[3],
                'visit_count': row[4],
                'crawl_depth': row[5],
                'status_code': row[6],
                'response_time': row[7],
                'content_length': row[8],
                'metadata': json.loads(row[9]) if row[9] else None
            })
        
        with open(filename, 'w') as f:
            json.dump(data, f, indent=2)
        
        return len(data)

# Example usage and testing
if __name__ == "__main__":
    # Create URL manager instance
    manager = URLManager()
    
    # Example: Add some test URLs
    test_urls = [
        "https://example.com/page1",
        "https://example.com/page2",
        "https://test.com/page1"
    ]
    
    for i, url in enumerate(test_urls):
        manager.add_url(
            url=url,
            crawl_depth=i,
            status_code=200,
            response_time=0.5 + i * 0.1,
            content_length=1000 + i * 100,
            metadata={'test': True, 'index': i}
        )
    
    # Print some statistics
    print("Database Stats:", manager.get_database_stats())
    print("Recent URLs:", manager.get_recent_urls(hours=1))
    print("Most Visited:", manager.get_most_visited_urls(5)) 