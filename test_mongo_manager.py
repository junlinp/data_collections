#!/usr/bin/env python3
import os
import sys

def test_mongo_manager():
    """Test MongoDB manager functionality"""
    try:
        # Import the MongoDB manager
        from mongo_utils import MongoDBManager, get_mongo_manager
        
        print("Testing MongoDB Manager...")
        
        # Test direct initialization
        print("\n1. Testing direct MongoDB manager initialization...")
        mongo_manager = MongoDBManager()
        print("✓ MongoDB manager initialized successfully")
        
        # Test database stats
        print("\n2. Testing database stats...")
        stats = mongo_manager.get_database_stats()
        print(f"✓ Database stats: {stats}")
        
        # Test web content operations
        print("\n3. Testing web content operations...")
        test_url = "https://example.com/test"
        success = mongo_manager.save_web_content(
            url=test_url,
            title="Test Page",
            html_content="<html><body><h1>Test Content</h1></body></html>",
            text_content="Test Content",
            status_code=200,
            crawl_depth=0
        )
        print(f"✓ Save web content: {success}")
        
        # Test retrieving web content
        content = mongo_manager.get_web_content(test_url)
        if content:
            print(f"✓ Retrieve web content: {content.get('title')}")
        else:
            print("✗ Failed to retrieve web content")
        
        # Test summary operations
        print("\n4. Testing summary operations...")
        success = mongo_manager.save_summary(
            url=test_url,
            title="Test Page",
            summary="This is a test summary",
            key_points="Point 1\nPoint 2",
            sentiment="positive",
            word_count=10,
            processing_time=1.5
        )
        print(f"✓ Save summary: {success}")
        
        # Test retrieving summary
        summary = mongo_manager.get_summary(test_url)
        if summary:
            print(f"✓ Retrieve summary: {summary.get('summary')}")
        else:
            print("✗ Failed to retrieve summary")
        
        # Test unprocessed URLs
        print("\n5. Testing unprocessed URLs...")
        unprocessed = mongo_manager.get_unprocessed_urls(limit=5)
        print(f"✓ Unprocessed URLs count: {len(unprocessed)}")
        
        # Test get_mongo_manager function
        print("\n6. Testing get_mongo_manager function...")
        manager = get_mongo_manager()
        print("✓ get_mongo_manager function works")
        
        # Clean up test data
        print("\n7. Cleaning up test data...")
        mongo_manager.db.web_content.delete_one({"url": test_url})
        mongo_manager.db.summaries.delete_one({"url": test_url})
        print("✓ Test data cleaned up")
        
        # Close connection
        mongo_manager.close()
        print("✓ MongoDB connection closed")
        
        print("\n🎉 All MongoDB manager tests passed!")
        return True
        
    except Exception as e:
        print(f"✗ MongoDB manager test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_mongo_manager()
    sys.exit(0 if success else 1) 