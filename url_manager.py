from datetime import datetime, timedelta
from urllib.parse import urlparse
import json
from mongo_utils import get_mongo_manager

class URLManager:
    def __init__(self):
        self.mongo_manager = get_mongo_manager()
        self.init_db()
    
    def init_db(self):
        """Initialize the MongoDB connection"""
        # MongoDB connection is already initialized in constructor
        pass
    
    def add_url(self, url, response_time=None, content_length=None, metadata=None):
        """Add or update a URL in the history using MongoDB"""
        try:
            # For now, use a simple status approach
            status = f"response_time:{response_time}"
            if metadata:
                status += f",metadata:{json.dumps(metadata)}"
            
            # Save to MongoDB using existing method
            result = self.mongo_manager.save_url_history(url, status)
            return result is not None
            
        except Exception as e:
            print(f"Error adding URL to history: {e}")
            return False
    
    def get_url_info(self, url):
        """Get information about a specific URL from MongoDB"""
        try:
            history = self.mongo_manager.get_url_history(url, limit=1)
            if history:
                latest = history[0]
                return {
                    'url': latest.get('url'),
                    'domain': self.extract_domain(latest.get('url', '')),
                    'first_visited': latest.get('created_at'),
                    'last_visited': latest.get('created_at'),
                    'visit_count': 1,  # Simplified for now
                    'response_time': None,  # Would need to parse from status
                    'content_length': None,
                    'metadata': None  # Would need to parse from status
                }
            return None
        except Exception as e:
            print(f"Error getting URL info: {e}")
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