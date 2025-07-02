#!/usr/bin/env python3
"""
Test script for MongoDB integration
"""

import os
import sys

def test_mongodb_connection():
    """Test MongoDB connection using environment variables"""
    try:
        # Get MongoDB connection details from environment
        mongodb_uri = os.getenv('MONGODB_URI')
        mongodb_database = os.getenv('MONGODB_DATABASE')
        
        print(f"MongoDB URI: {mongodb_uri}")
        print(f"MongoDB Database: {mongodb_database}")
        
        # Try to import pymongo
        try:
            import pymongo
            print("✓ pymongo is available")
            
            # Test connection
            client = pymongo.MongoClient(mongodb_uri)
            db = client[mongodb_database]
            
            # Test ping
            result = db.command('ping')
            print(f"✓ MongoDB ping successful: {result}")
            
            # List collections
            collections = db.list_collection_names()
            print(f"✓ Collections in {mongodb_database}: {collections}")
            
            # Test insert and find
            test_collection = db.test_connection
            test_doc = {"test": "connection", "timestamp": "2025-07-02"}
            result = test_collection.insert_one(test_doc)
            print(f"✓ Insert test document: {result.inserted_id}")
            
            # Find the document
            found_doc = test_collection.find_one({"test": "connection"})
            print(f"✓ Found test document: {found_doc}")
            
            # Clean up
            test_collection.delete_one({"test": "connection"})
            print("✓ Cleaned up test document")
            
            client.close()
            print("✓ MongoDB connection test completed successfully")
            return True
            
        except ImportError:
            print("✗ pymongo is not available")
            return False
            
    except Exception as e:
        print(f"✗ MongoDB connection test failed: {e}")
        return False

if __name__ == "__main__":
    success = test_mongodb_connection()
    sys.exit(0 if success else 1) 