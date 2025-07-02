"""
MongoDB utilities for web crawler system
Handles database connections and operations
"""

import os
import logging
from datetime import datetime
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure, DuplicateKeyError, OperationFailure

logger = logging.getLogger(__name__)

class MongoDBManager:
    def __init__(self, uri=None, database=None):
        """Initialize MongoDB connection"""
        self.uri = uri or os.getenv('MONGODB_URI', 'mongodb://admin:password123@mongodb:27017/crawler_db?authSource=admin')
        self.database_name = database or os.getenv('MONGODB_DATABASE', 'crawler_db')
        self.client = None
        self.db = None
        self.connect()
    
    def connect(self):
        """Establish connection to MongoDB"""
        try:
            self.client = MongoClient(self.uri, serverSelectionTimeoutMS=5000)
            # Test the connection
            self.client.admin.command('ping')
            self.db = self.client[self.database_name]
            logger.info(f"Successfully connected to MongoDB database: {self.database_name}")
        except ConnectionFailure as e:
            logger.error(f"Failed to connect to MongoDB: {e}")
            raise
    
    def close(self):
        """Close MongoDB connection"""
        if self.client:
            self.client.close()
            logger.info("MongoDB connection closed")
    
    def save_web_content(self, url, title, html_content, text_content, status_code, crawl_depth, parent_url=None):
        """Save web content to MongoDB"""
        try:
            content_doc = {
                'url': url,
                'title': title,
                'html_content': html_content,
                'text_content': text_content,
                'status_code': status_code,
                'crawl_depth': crawl_depth,
                'parent_url': parent_url,
                'created_at': datetime.utcnow(),
                'updated_at': datetime.utcnow()
            }
            
            # Use upsert to handle duplicates
            result = self.db.web_content.update_one(
                {'url': url},
                {'$set': content_doc},
                upsert=True
            )
            
            if result.upserted_id:
                logger.info(f"Saved new content for URL: {url}")
            else:
                logger.info(f"Updated existing content for URL: {url}")
            
            return True
        except Exception as e:
            logger.error(f"Error saving web content for {url}: {e}")
            return False
    
    def get_web_content(self, url):
        """Get web content by URL"""
        try:
            content = self.db.web_content.find_one({'url': url})
            return content
        except Exception as e:
            logger.error(f"Error getting web content for {url}: {e}")
            return None
    
    def get_all_web_content(self, limit=None, skip=0):
        """Get all web content with pagination"""
        try:
            query = self.db.web_content.find().sort('created_at', -1)
            if skip > 0:
                query = query.skip(skip)
            if limit:
                query = query.limit(limit)
            return list(query)
        except Exception as e:
            logger.error(f"Error getting all web content: {e}")
            return []
    
    def count_web_content(self):
        """Count total web content documents"""
        try:
            return self.db.web_content.count_documents({})
        except Exception as e:
            logger.error(f"Error counting web content: {e}")
            return 0
    
    def save_url_history(self, url, status):
        """Save URL history"""
        try:
            history_doc = {
                'url': url,
                'status': status,
                'created_at': datetime.utcnow()
            }
            
            result = self.db.url_history.insert_one(history_doc)
            logger.info(f"Saved URL history for {url}: {status}")
            return result.inserted_id
        except Exception as e:
            logger.error(f"Error saving URL history for {url}: {e}")
            return None
    
    def get_url_history(self, url, limit=10):
        """Get URL history for a specific URL"""
        try:
            history = self.db.url_history.find(
                {'url': url}
            ).sort('created_at', -1).limit(limit)
            return list(history)
        except Exception as e:
            logger.error(f"Error getting URL history for {url}: {e}")
            return []
    
    def save_summary(self, url, title, summary, key_points=None, sentiment=None, word_count=None, processing_time=None):
        """Save summary to MongoDB"""
        try:
            summary_doc = {
                'url': url,
                'title': title,
                'summary': summary,
                'key_points': key_points,
                'sentiment': sentiment,
                'word_count': word_count,
                'processing_time': processing_time,
                'created_at': datetime.utcnow(),
                'updated_at': datetime.utcnow()
            }
            
            result = self.db.summaries.update_one(
                {'url': url},
                {'$set': summary_doc},
                upsert=True
            )
            
            if result.upserted_id:
                logger.info(f"Saved new summary for URL: {url}")
            else:
                logger.info(f"Updated existing summary for URL: {url}")
            
            return True
        except Exception as e:
            logger.error(f"Error saving summary for {url}: {e}")
            return False
    
    def get_summary(self, url):
        """Get summary by URL"""
        try:
            summary = self.db.summaries.find_one({'url': url})
            return summary
        except Exception as e:
            logger.error(f"Error getting summary for {url}: {e}")
            return None
    
    def get_all_summaries(self, limit=None, skip=0):
        """Get all summaries with pagination"""
        try:
            query = self.db.summaries.find().sort('created_at', -1)
            if skip > 0:
                query = query.skip(skip)
            if limit:
                query = query.limit(limit)
            return list(query)
        except Exception as e:
            logger.error(f"Error getting all summaries: {e}")
            return []
    
    def count_summaries(self):
        """Count total summary documents"""
        try:
            return self.db.summaries.count_documents({})
        except Exception as e:
            logger.error(f"Error counting summaries: {e}")
            return 0
    
    def get_unprocessed_urls(self, limit=None):
        """Get URLs that have content but no summary"""
        try:
            # Find URLs that exist in web_content but not in summaries
            pipeline = [
                {
                    '$lookup': {
                        'from': 'summaries',
                        'localField': 'url',
                        'foreignField': 'url',
                        'as': 'summary'
                    }
                },
                {
                    '$match': {
                        'summary': {'$size': 0}
                    }
                },
                {
                    '$project': {
                        'url': 1,
                        'title': 1,
                        'text_content': 1
                    }
                }
            ]
            
            if limit:
                pipeline.append({'$limit': limit})
            
            unprocessed = list(self.db.web_content.aggregate(pipeline))
            return unprocessed
        except Exception as e:
            logger.error(f"Error getting unprocessed URLs: {e}")
            return []
    
    def get_database_stats(self):
        """Get database statistics"""
        try:
            stats = {
                'web_content_count': self.db.web_content.count_documents({}),
                'url_history_count': self.db.url_history.count_documents({}),
                'summaries_count': self.db.summaries.count_documents({}),
                'unprocessed_count': len(self.get_unprocessed_urls())
            }
            return stats
        except Exception as e:
            logger.error(f"Error getting database stats: {e}")
            return {}

# Global MongoDB manager instance
mongo_manager = None

def get_mongo_manager():
    """Get or create MongoDB manager instance"""
    global mongo_manager
    if mongo_manager is None:
        mongo_manager = MongoDBManager()
    return mongo_manager 