#!/usr/bin/env python3
"""
Test script for the new queue-based crawler system
Tests the queue manager, worker system, and API endpoints
"""

import requests
import time
import json
import sys

# Configuration
CRAWLER_SERVER_URL = "http://localhost:5001"
UI_SERVER_URL = "http://localhost:5000"

def test_health_check():
    """Test health check endpoint"""
    print("🔍 Testing health check...")
    try:
        response = requests.get(f"{CRAWLER_SERVER_URL}/api/health", timeout=5)
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Health check passed: {data}")
            return True
        else:
            print(f"❌ Health check failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Health check error: {e}")
        return False

def test_add_url_to_queue():
    """Test adding URL to queue"""
    print("\n🔍 Testing add URL to queue...")
    try:
        # Test URL that should be added
        test_url = "https://httpbin.org/html"
        response = requests.post(
            f"{CRAWLER_SERVER_URL}/api/add-url",
            json={"url": test_url, "priority": 0},
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            if data.get('success'):
                print(f"✅ URL added to queue: {data['message']}")
                return True
            else:
                print(f"❌ URL not added: {data.get('error', 'Unknown error')}")
                return False
        else:
            print(f"❌ Add URL failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Add URL error: {e}")
        return False

def test_queue_stats():
    """Test getting queue statistics"""
    print("\n🔍 Testing queue statistics...")
    try:
        response = requests.get(f"{CRAWLER_SERVER_URL}/api/queue-stats", timeout=5)
        if response.status_code == 200:
            data = response.json()
            if data.get('success'):
                stats = data['data']
                print(f"✅ Queue stats: {stats}")
                return True
            else:
                print(f"❌ Queue stats failed: {data.get('error', 'Unknown error')}")
                return False
        else:
            print(f"❌ Queue stats failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Queue stats error: {e}")
        return False

def test_worker_stats():
    """Test getting worker statistics"""
    print("\n🔍 Testing worker statistics...")
    try:
        response = requests.get(f"{CRAWLER_SERVER_URL}/api/worker-stats", timeout=5)
        if response.status_code == 200:
            data = response.json()
            if data.get('success'):
                stats = data['data']
                print(f"✅ Worker stats: {stats}")
                return True
            else:
                print(f"❌ Worker stats failed: {data.get('error', 'Unknown error')}")
                return False
        else:
            print(f"❌ Worker stats failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Worker stats error: {e}")
        return False

def test_pending_urls():
    """Test getting pending URLs"""
    print("\n🔍 Testing pending URLs...")
    try:
        response = requests.get(f"{CRAWLER_SERVER_URL}/api/pending-urls", timeout=5)
        if response.status_code == 200:
            data = response.json()
            if data.get('success'):
                urls = data['data']
                print(f"✅ Pending URLs: {len(urls)} found")
                for url in urls[:3]:  # Show first 3
                    print(f"  - {url['url']} (Priority: {url['priority']})")
                return True
            else:
                print(f"❌ Pending URLs failed: {data.get('error', 'Unknown error')}")
                return False
        else:
            print(f"❌ Pending URLs failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Pending URLs error: {e}")
        return False

def test_24_hour_rule():
    """Test 24-hour rule by adding same URL twice"""
    print("\n🔍 Testing 24-hour rule...")
    try:
        test_url = "https://httpbin.org/json"
        
        # Add URL first time
        response1 = requests.post(
            f"{CRAWLER_SERVER_URL}/api/add-url",
            json={"url": test_url, "priority": 0},
            timeout=10
        )
        
        if response1.status_code == 200:
            data1 = response1.json()
            print(f"First add: {data1['message']}")
            
            # Try to add same URL again immediately
            response2 = requests.post(
                f"{CRAWLER_SERVER_URL}/api/add-url",
                json={"url": test_url, "priority": 0},
                timeout=10
            )
            
            if response2.status_code == 200:
                data2 = response2.json()
                if not data2.get('success') and "24 hours" in data2.get('message', ''):
                    print(f"✅ 24-hour rule working: {data2['message']}")
                    return True
                else:
                    print(f"❌ 24-hour rule not working: {data2}")
                    return False
            else:
                print(f"❌ Second add failed: {response2.status_code}")
                return False
        else:
            print(f"❌ First add failed: {response1.status_code}")
            return False
    except Exception as e:
        print(f"❌ 24-hour rule test error: {e}")
        return False

def test_worker_management():
    """Test worker management functions"""
    print("\n🔍 Testing worker management...")
    try:
        # Test starting workers
        response = requests.post(
            f"{CRAWLER_SERVER_URL}/api/start-workers",
            json={"num_workers": 2},
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            if data.get('success'):
                print(f"✅ Workers started: {data['message']}")
                
                # Wait a moment for workers to start
                time.sleep(2)
                
                # Check worker stats
                stats_response = requests.get(f"{CRAWLER_SERVER_URL}/api/worker-stats", timeout=5)
                if stats_response.status_code == 200:
                    stats_data = stats_response.json()
                    if stats_data.get('success'):
                        stats = stats_data['data']
                        running_workers = sum(1 for w in stats.get('workers', {}).values() if w.get('running'))
                        print(f"✅ {running_workers} workers running")
                        return True
                
                return True
            else:
                print(f"❌ Start workers failed: {data.get('error', 'Unknown error')}")
                return False
        else:
            print(f"❌ Start workers failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Worker management error: {e}")
        return False

def test_crawled_data():
    """Test getting crawled data"""
    print("\n🔍 Testing crawled data...")
    try:
        response = requests.get(f"{CRAWLER_SERVER_URL}/api/crawled-data", timeout=5)
        if response.status_code == 200:
            data = response.json()
            if data.get('success'):
                items = data['data']
                print(f"✅ Crawled data: {len(items)} items found")
                if items:
                    print(f"  Sample item: {items[0]['url']}")
                return True
            else:
                print(f"❌ Crawled data failed: {data.get('error', 'Unknown error')}")
                return False
        else:
            print(f"❌ Crawled data failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Crawled data error: {e}")
        return False

def test_ui_server():
    """Test UI server endpoints"""
    print("\n🔍 Testing UI server...")
    try:
        # Test UI health check
        response = requests.get(f"{UI_SERVER_URL}/api/health", timeout=5)
        if response.status_code == 200:
            data = response.json()
            print(f"✅ UI server health: {data}")
            return True
        else:
            print(f"❌ UI server health failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ UI server error: {e}")
        return False

def main():
    """Run all tests"""
    print("🚀 Testing Queue-Based Crawler System")
    print("=" * 50)
    
    tests = [
        ("Health Check", test_health_check),
        ("Add URL to Queue", test_add_url_to_queue),
        ("Queue Statistics", test_queue_stats),
        ("Worker Statistics", test_worker_stats),
        ("Pending URLs", test_pending_urls),
        ("24-Hour Rule", test_24_hour_rule),
        ("Worker Management", test_worker_management),
        ("Crawled Data", test_crawled_data),
        ("UI Server", test_ui_server),
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        try:
            if test_func():
                passed += 1
            else:
                print(f"❌ {test_name} failed")
        except Exception as e:
            print(f"❌ {test_name} error: {e}")
    
    print("\n" + "=" * 50)
    print(f"📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! Queue-based system is working correctly.")
        return 0
    else:
        print("⚠️  Some tests failed. Check the logs above for details.")
        return 1

if __name__ == "__main__":
    sys.exit(main()) 