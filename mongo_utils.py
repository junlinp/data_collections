"""
MongoDB utilities for web crawler system
Handles database connections and operations
"""

import os
import logging
import time
import sys
import traceback
from datetime import datetime
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure, DuplicateKeyError, OperationFailure, ServerSelectionTimeoutError

# Configure logging with more detailed format
logging.basicConfig(
    level=logging.INFO, 
    format='%(asctime)s - %(name)s - %(levelname)s - [PID:%(process)d] - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('/app/data/mongo_utils.log', mode='a')
    ]
)
logger = logging.getLogger(__name__)

class MongoDBManager:
    def __init__(self, uri=None, database=None):
        """Initialize MongoDB connection"""
        self.uri = uri or os.getenv('MONGODB_URI', 'mongodb://admin:password123@mongodb:27017/crawler_db?authSource=admin')
        self.database_name = database or os.getenv('MONGODB_DATABASE', 'crawler_db')
        self.client = None
        self.db = None
        self.connection_attempts = 0
        self.last_connection_error = None
        self.connection_established_at = None
        self.operation_count = 0
        self.error_count = 0
        
        logger.info(f"🚀 Initializing MongoDB manager for database: {self.database_name}")
        logger.info(f"MongoDB URI: {self.uri}")
        
        self.connect()
    
    def connect(self):
        """Establish connection to MongoDB with retry logic"""
        max_retries = 5
        retry_delay = 2
        
        for attempt in range(max_retries):
            try:
                self.connection_attempts += 1
                logger.info(f"📡 MongoDB connection attempt {attempt + 1}/{max_retries}")
                
                # Set connection timeout and server selection timeout
                self.client = MongoClient(
                    self.uri, 
                    serverSelectionTimeoutMS=10000,
                    connectTimeoutMS=10000,
                    socketTimeoutMS=10000,
                    maxPoolSize=10,
                    minPoolSize=1
                )
                
                # Test the connection
                start_time = time.time()
                self.client.admin.command('ping')
                ping_time = time.time() - start_time
                
                self.db = self.client[self.database_name]
                self.connection_established_at = datetime.utcnow()
                
                # Test a simple operation
                collections = self.db.list_collection_names()
                
                logger.info(f"✅ Successfully connected to MongoDB database: {self.database_name}")
                logger.info(f"📊 Connection details - Ping time: {ping_time:.3f}s, Collections: {len(collections)}")
                logger.info(f"📊 Collections found: {collections}")
                
                return True
                
            except ServerSelectionTimeoutError as e:
                self.last_connection_error = str(e)
                logger.error(f"❌ MongoDB server selection timeout (attempt {attempt + 1}): {e}")
                if attempt < max_retries - 1:
                    logger.info(f"⏳ Retrying in {retry_delay} seconds...")
                    time.sleep(retry_delay)
                    retry_delay *= 2  # Exponential backoff
                else:
                    logger.critical(f"❌ MongoDB connection failed after {max_retries} attempts")
                    raise
                    
            except ConnectionFailure as e:
                self.last_connection_error = str(e)
                logger.error(f"❌ MongoDB connection failure (attempt {attempt + 1}): {e}")
                logger.error(traceback.format_exc())
                if attempt < max_retries - 1:
                    logger.info(f"⏳ Retrying in {retry_delay} seconds...")
                    time.sleep(retry_delay)
                    retry_delay *= 2
                else:
                    logger.critical(f"❌ MongoDB connection failed after {max_retries} attempts")
                    raise
                    
            except Exception as e:
                self.last_connection_error = str(e)
                logger.error(f"❌ Unexpected MongoDB connection error (attempt {attempt + 1}): {e}")
                logger.error(traceback.format_exc())
                if attempt < max_retries - 1:
                    logger.info(f"⏳ Retrying in {retry_delay} seconds...")
                    time.sleep(retry_delay)
                    retry_delay *= 2
                else:
                    logger.critical(f"❌ MongoDB connection failed after {max_retries} attempts")
                    raise
    
    def test_connection(self):
        """Test MongoDB connection health"""
        try:
            if not self.client:
                return False
                
            start_time = time.time()
            self.client.admin.command('ping')
            ping_time = time.time() - start_time
            
            logger.debug(f"✅ MongoDB ping successful: {ping_time:.3f}s")
            return True
            
        except Exception as e:
            logger.error(f"❌ MongoDB connection test failed: {e}")
            return False
    
    def ensure_connection(self):
        """Ensure MongoDB connection is active, reconnect if necessary"""
        if not self.test_connection():
            logger.warning("🔄 MongoDB connection lost, attempting to reconnect...")
            try:
                self.connect()
                logger.info("✅ MongoDB reconnection successful")
            except Exception as e:
                logger.error(f"❌ MongoDB reconnection failed: {e}")
                raise
    
    def close(self):
        """Close MongoDB connection"""
        if self.client:
            self.client.close()
            logger.info("🔌 MongoDB connection closed")
            logger.info(f"📊 Final stats - Operations: {self.operation_count}, Errors: {self.error_count}")
    
    def _execute_operation(self, operation_name, operation_func):
        """Execute MongoDB operation with error handling and monitoring"""
        start_time = time.time()
        self.operation_count += 1
        
        try:
            self.ensure_connection()
            result = operation_func()
            
            elapsed = time.time() - start_time
            logger.debug(f"✅ MongoDB operation '{operation_name}' completed in {elapsed:.3f}s")
            
            return result
            
        except Exception as e:
            self.error_count += 1
            elapsed = time.time() - start_time
            logger.error(f"❌ MongoDB operation '{operation_name}' failed after {elapsed:.3f}s: {e}")
            logger.error(traceback.format_exc())
            
            # Log connection status
            logger.info(f"🔍 Connection status - Attempts: {self.connection_attempts}, "
                       f"Established: {self.connection_established_at}, "
                       f"Last error: {self.last_connection_error}")
            
            raise
    
    def save_web_content(self, url, title, html_content, text_content, parent_url=None):
        """Save web content to MongoDB"""
        def operation():
            content_doc = {
                'url': url,
                'title': title,
                'html_content': html_content,
                'text_content': text_content,
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
                logger.info(f"💾 Saved new content for URL: {url}")
            else:
                logger.info(f"🔄 Updated existing content for URL: {url}")
            
            return True
        
        try:
            return self._execute_operation('save_web_content', operation)
        except Exception as e:
            logger.error(f"❌ Error saving web content for {url}: {e}")
            return False
    
    def get_web_content(self, url):
        """Get web content by URL"""
        def operation():
            content = self.db.web_content.find_one({'url': url})
            return content
        
        try:
            return self._execute_operation('get_web_content', operation)
        except Exception as e:
            logger.error(f"❌ Error getting web content for {url}: {e}")
            return None
    
    def get_all_web_content(self, limit=None, skip=0):
        """Get all web content with pagination"""
        def operation():
            query = self.db.web_content.find().sort('created_at', -1)
            if skip > 0:
                query = query.skip(skip)
            if limit:
                query = query.limit(limit)
            return list(query)
        
        try:
            return self._execute_operation('get_all_web_content', operation)
        except Exception as e:
            logger.error(f"❌ Error getting all web content: {e}")
            return []
    
    def count_web_content(self):
        """Count total web content documents"""
        def operation():
            return self.db.web_content.count_documents({})
        
        try:
            return self._execute_operation('count_web_content', operation)
        except Exception as e:
            logger.error(f"❌ Error counting web content: {e}")
            return 0
    
    def save_url_history(self, url, status):
        """Save URL history"""
        def operation():
            history_doc = {
                'url': url,
                'status': status,
                'created_at': datetime.utcnow()
            }
            
            result = self.db.url_history.insert_one(history_doc)
            logger.info(f"📝 Saved URL history for {url}: {status}")
            return result.inserted_id
        
        try:
            return self._execute_operation('save_url_history', operation)
        except Exception as e:
            logger.error(f"❌ Error saving URL history for {url}: {e}")
            return None
    
    def get_url_history(self, url, limit=10):
        """Get URL history for a specific URL"""
        def operation():
            history = self.db.url_history.find(
                {'url': url}
            ).sort('created_at', -1).limit(limit)
            return list(history)
        
        try:
            return self._execute_operation('get_url_history', operation)
        except Exception as e:
            logger.error(f"❌ Error getting URL history for {url}: {e}")
            return []
    
    def save_summary(self, url, title, summary, key_points=None, sentiment=None, word_count=None, processing_time=None):
        """Save summary to MongoDB"""
        def operation():
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
                logger.info(f"💾 Saved new summary for URL: {url}")
            else:
                logger.info(f"🔄 Updated existing summary for URL: {url}")
            
            return True
        
        try:
            return self._execute_operation('save_summary', operation)
        except Exception as e:
            logger.error(f"❌ Error saving summary for {url}: {e}")
            return False
    
    def get_summary(self, url):
        """Get summary by URL"""
        def operation():
            summary = self.db.summaries.find_one({'url': url})
            return summary
        
        try:
            return self._execute_operation('get_summary', operation)
        except Exception as e:
            logger.error(f"❌ Error getting summary for {url}: {e}")
            return None
    
    def get_all_summaries(self, limit=None, skip=0):
        """Get all summaries with pagination"""
        def operation():
            query = self.db.summaries.find().sort('created_at', -1)
            if skip > 0:
                query = query.skip(skip)
            if limit:
                query = query.limit(limit)
            return list(query)
        
        try:
            return self._execute_operation('get_all_summaries', operation)
        except Exception as e:
            logger.error(f"❌ Error getting all summaries: {e}")
            return []
    
    def count_summaries(self):
        """Count total summary documents"""
        def operation():
            return self.db.summaries.count_documents({})
        
        try:
            return self._execute_operation('count_summaries', operation)
        except Exception as e:
            logger.error(f"❌ Error counting summaries: {e}")
            return 0
    
    def get_unprocessed_urls(self, limit=None):
        """Get URLs that have content but no summary"""
        def operation():
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
                        'text_content': 1,
                        'html_content': 1
                    }
                }
            ]
            
            if limit:
                pipeline.append({'$limit': limit})
            
            unprocessed = list(self.db.web_content.aggregate(pipeline))
            return unprocessed
        
        try:
            return self._execute_operation('get_unprocessed_urls', operation)
        except Exception as e:
            logger.error(f"❌ Error getting unprocessed URLs: {e}")
            return []
    
    def get_database_stats(self):
        """Get database statistics"""
        def operation():
            start_time = time.time()
            
            stats = {
                'web_content_count': self.db.web_content.count_documents({}),
                'url_history_count': self.db.url_history.count_documents({}),
                'summaries_count': self.db.summaries.count_documents({}),
                'connection_attempts': self.connection_attempts,
                'operation_count': self.operation_count,
                'error_count': self.error_count,
                'connection_established_at': self.connection_established_at,
                'last_connection_error': self.last_connection_error
            }
            
            # Add unprocessed count (this is expensive so we do it last)
            try:
                stats['unprocessed_count'] = len(self.get_unprocessed_urls())
            except Exception as e:
                logger.warning(f"⚠️ Could not get unprocessed count: {e}")
                stats['unprocessed_count'] = -1
            
            elapsed = time.time() - start_time
            logger.info(f"📊 Database stats retrieved in {elapsed:.3f}s: {stats}")
            
            return stats
        
        try:
            return self._execute_operation('get_database_stats', operation)
        except Exception as e:
            logger.error(f"❌ Error getting database stats: {e}")
            return {
                'error': str(e),
                'connection_attempts': self.connection_attempts,
                'operation_count': self.operation_count,
                'error_count': self.error_count
            }
    
    def get_health_status(self):
        """Get detailed health status for monitoring"""
        try:
            health = {
                'connected': self.test_connection(),
                'connection_attempts': self.connection_attempts,
                'operation_count': self.operation_count,
                'error_count': self.error_count,
                'connection_established_at': self.connection_established_at,
                'last_connection_error': self.last_connection_error,
                'uptime_seconds': (datetime.utcnow() - self.connection_established_at).total_seconds() if self.connection_established_at else 0
            }
            
            return health
        except Exception as e:
            logger.error(f"❌ Error getting health status: {e}")
            return {'error': str(e), 'connected': False}

# Global MongoDB manager instance
mongo_manager = None

def get_mongo_manager():
    """Get or create MongoDB manager instance"""
    global mongo_manager
    if mongo_manager is None:
        logger.info("🔄 Creating new MongoDB manager instance")
        mongo_manager = MongoDBManager()
    return mongo_manager 