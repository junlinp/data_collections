#!/usr/bin/env python3
"""
Migration script to transfer data from SQLite databases to MongoDB
"""

import sqlite3
import os
import sys
from datetime import datetime
import json
from mongo_utils import MongoDBManager

# Patch: Set MongoDB URI to localhost for host-based migration
os.environ['MONGODB_URI'] = 'mongodb://admin:password123@localhost:27017/crawler_db?authSource=admin'

def connect_sqlite_safely(db_path, timeout=30):
    """Connect to SQLite database with timeout to handle locks"""
    try:
        # Try to connect in read-only mode first
        conn = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True, timeout=timeout)
        return conn
    except sqlite3.OperationalError as e:
        print(f"Error connecting to {db_path}: {e}")
        return None

def migrate_web_content():
    """Migrate web content from web_crawler.db to MongoDB"""
    print("Migrating web content...")
    
    db_path = '/mnt/rbd0/crawler_data/web_crawler.db'
    if not os.path.exists(db_path):
        print(f"Database not found: {db_path}")
        return
    
    conn = connect_sqlite_safely(db_path)
    if not conn:
        return
    
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = cursor.fetchall()
        print(f"Tables found: {tables}")
        
        # Check if crawled_content table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='crawled_content'")
        if not cursor.fetchone():
            print("crawled_content table not found")
            return
        
        # Get total count
        cursor.execute("SELECT COUNT(*) FROM crawled_content")
        total_count = cursor.fetchone()[0]
        print(f"Total records to migrate: {total_count}")
        
        if total_count == 0:
            print("No records to migrate")
            return
        
        # Initialize MongoDB manager
        mongo_manager = MongoDBManager()
        
        # Migrate in batches
        batch_size = 100
        offset = 0
        migrated_count = 0
        
        while True:
            cursor.execute("""
                SELECT url, title, content, html_content, links, crawled_at, crawl_depth
                FROM crawled_content 
                ORDER BY crawled_at 
                LIMIT ? OFFSET ?
            """, (batch_size, offset))
            
            batch = cursor.fetchall()
            if not batch:
                break
            
            for row in batch:
                url, title, content, html_content, links, crawled_at, crawl_depth = row
                
                # Parse links if it's a string
                if links and isinstance(links, str):
                    links_list = links.split('\n') if links else []
                else:
                    links_list = []
                
                # Convert crawled_at to datetime if it's a string
                if isinstance(crawled_at, str):
                    try:
                        crawled_at = datetime.fromisoformat(crawled_at.replace('Z', '+00:00'))
                    except:
                        crawled_at = datetime.utcnow()
                
                # Save to MongoDB
                success = mongo_manager.save_web_content(
                    url=url,
                    title=title or '',
                    html_content=html_content or '',
                    text_content=content or '',
                    status_code=200,  # Default status code
                    crawl_depth=crawl_depth or 0
                )
                
                if success:
                    migrated_count += 1
                    if migrated_count % 100 == 0:
                        print(f"Migrated {migrated_count}/{total_count} records")
            
            offset += batch_size
        
        print(f"Web content migration completed: {migrated_count} records migrated")
        
    except Exception as e:
        print(f"Error migrating web content: {e}")
    finally:
        conn.close()

def migrate_summaries():
    """Migrate summaries from summaries.db to MongoDB"""
    print("Migrating summaries...")
    
    db_path = '/mnt/rbd0/crawler_data/summaries.db'
    if not os.path.exists(db_path):
        print(f"Database not found: {db_path}")
        return
    
    conn = connect_sqlite_safely(db_path)
    if not conn:
        return
    
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = cursor.fetchall()
        print(f"Tables found: {tables}")
        
        # Check if summaries table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='summaries'")
        if not cursor.fetchone():
            print("summaries table not found")
            return
        
        # Get total count
        cursor.execute("SELECT COUNT(*) FROM summaries")
        total_count = cursor.fetchone()[0]
        print(f"Total summaries to migrate: {total_count}")
        
        if total_count == 0:
            print("No summaries to migrate")
            return
        
        # Initialize MongoDB manager
        mongo_manager = MongoDBManager()
        
        # Migrate in batches
        batch_size = 100
        offset = 0
        migrated_count = 0
        
        while True:
            cursor.execute("""
                SELECT url, title, summary, key_points, sentiment, word_count, processing_time, created_at
                FROM summaries 
                ORDER BY created_at 
                LIMIT ? OFFSET ?
            """, (batch_size, offset))
            
            batch = cursor.fetchall()
            if not batch:
                break
            
            for row in batch:
                url, title, summary, key_points, sentiment, word_count, processing_time, created_at = row
                
                # Convert created_at to datetime if it's a string
                if isinstance(created_at, str):
                    try:
                        created_at = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
                    except:
                        created_at = datetime.utcnow()
                
                # Save to MongoDB
                success = mongo_manager.save_summary(
                    url=url,
                    title=title or '',
                    summary=summary or '',
                    key_points=key_points or '',
                    sentiment=sentiment or 'neutral',
                    word_count=word_count or 0,
                    processing_time=processing_time or 0.0
                )
                
                if success:
                    migrated_count += 1
                    if migrated_count % 100 == 0:
                        print(f"Migrated {migrated_count}/{total_count} summaries")
            
            offset += batch_size
        
        print(f"Summaries migration completed: {migrated_count} records migrated")
        
    except Exception as e:
        print(f"Error migrating summaries: {e}")
    finally:
        conn.close()

def migrate_url_history():
    """Migrate URL history from url_history.db to MongoDB"""
    print("Migrating URL history...")
    
    db_path = '/mnt/rbd0/crawler_data/url_history.db'
    if not os.path.exists(db_path):
        print(f"Database not found: {db_path}")
        return
    
    conn = connect_sqlite_safely(db_path)
    if not conn:
        return
    
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = cursor.fetchall()
        print(f"Tables found: {tables}")
        
        # Check if url_history table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='url_history'")
        if not cursor.fetchone():
            print("url_history table not found")
            return
        
        # Get total count
        cursor.execute("SELECT COUNT(*) FROM url_history")
        total_count = cursor.fetchone()[0]
        print(f"Total URL history records to migrate: {total_count}")
        
        if total_count == 0:
            print("No URL history to migrate")
            return
        
        # Initialize MongoDB manager
        mongo_manager = MongoDBManager()
        
        # Migrate in batches
        batch_size = 100
        offset = 0
        migrated_count = 0
        
        while True:
            cursor.execute("""
                SELECT url, domain, first_visited, last_visited, visit_count, crawl_depth, status_code, response_time, content_length, metadata
                FROM url_history 
                ORDER BY last_visited 
                LIMIT ? OFFSET ?
            """, (batch_size, offset))
            
            batch = cursor.fetchall()
            if not batch:
                break
            
            for row in batch:
                url, domain, first_visited, last_visited, visit_count, crawl_depth, status_code, response_time, content_length, metadata = row
                
                # Parse metadata if it's a JSON string
                metadata_dict = None
                if metadata and isinstance(metadata, str):
                    try:
                        metadata_dict = json.loads(metadata)
                    except:
                        metadata_dict = None
                
                # Convert timestamps to datetime
                if isinstance(first_visited, str):
                    try:
                        first_visited = datetime.fromisoformat(first_visited.replace('Z', '+00:00'))
                    except:
                        first_visited = datetime.utcnow()
                
                if isinstance(last_visited, str):
                    try:
                        last_visited = datetime.fromisoformat(last_visited.replace('Z', '+00:00'))
                    except:
                        last_visited = datetime.utcnow()
                
                # Save to MongoDB (using save_url_history method)
                history_doc = {
                    'url': url,
                    'domain': domain,
                    'first_visited': first_visited,
                    'last_visited': last_visited,
                    'visit_count': visit_count or 1,
                    'crawl_depth': crawl_depth or 0,
                    'status_code': status_code,
                    'response_time': response_time,
                    'content_length': content_length,
                    'metadata': metadata_dict,
                    'created_at': datetime.utcnow()
                }
                
                try:
                    result = mongo_manager.db.url_history.insert_one(history_doc)
                    if result.inserted_id:
                        migrated_count += 1
                        if migrated_count % 100 == 0:
                            print(f"Migrated {migrated_count}/{total_count} URL history records")
                except Exception as e:
                    print(f"Error saving URL history for {url}: {e}")
            
            offset += batch_size
        
        print(f"URL history migration completed: {migrated_count} records migrated")
        
    except Exception as e:
        print(f"Error migrating URL history: {e}")
    finally:
        conn.close()

def main():
    """Main migration function"""
    print("Starting SQLite to MongoDB migration...")
    print("=" * 50)
    
    # Check if MongoDB is accessible
    try:
        mongo_manager = MongoDBManager()
        print("✓ MongoDB connection successful")
    except Exception as e:
        print(f"✗ MongoDB connection failed: {e}")
        return
    
    # Migrate each database
    migrate_web_content()
    print("-" * 30)
    
    migrate_summaries()
    print("-" * 30)
    
    migrate_url_history()
    print("-" * 30)
    
    print("Migration completed!")
    
    # Show final stats
    try:
        stats = mongo_manager.get_database_stats()
        print(f"Final MongoDB stats: {stats}")
    except Exception as e:
        print(f"Error getting final stats: {e}")

if __name__ == "__main__":
    main() 