#!/usr/bin/env python3
"""
Test script for the updated web API endpoints
"""

import requests
import json
import time

def test_api_endpoints():
    """Test the new API endpoints"""
    base_url = "http://localhost:5000"
    
    print("🧪 Testing Web API Endpoints...")
    
    # Test 1: Get queue state
    print("\n1. Testing /api/queue-state")
    try:
        response = requests.get(f"{base_url}/api/queue-state")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Queue state API working: {data['success']}")
        else:
            print(f"❌ Queue state API failed: {response.status_code}")
    except Exception as e:
        print(f"❌ Queue state API error: {e}")
    
    # Test 2: Get global queue state
    print("\n2. Testing /api/global-queue-state")
    try:
        response = requests.get(f"{base_url}/api/global-queue-state")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Global queue state API working: {data['success']}")
        else:
            print(f"❌ Global queue state API failed: {response.status_code}")
    except Exception as e:
        print(f"❌ Global queue state API error: {e}")
    
    # Test 3: Get crawled data
    print("\n3. Testing /api/crawled-data")
    try:
        response = requests.get(f"{base_url}/api/crawled-data?page=1&per_page=5")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Crawled data API working: {data['success']}")
            print(f"   Total items: {data['data']['total']}")
        else:
            print(f"❌ Crawled data API failed: {response.status_code}")
    except Exception as e:
        print(f"❌ Crawled data API error: {e}")
    
    # Test 4: Get URL history stats
    print("\n4. Testing /api/stats")
    try:
        response = requests.get(f"{base_url}/api/stats")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Stats API working: {data['success']}")
        else:
            print(f"❌ Stats API failed: {response.status_code}")
    except Exception as e:
        print(f"❌ Stats API error: {e}")
    
    # Test 5: Test start crawl API (without actually starting)
    print("\n5. Testing /api/start-crawl (validation)")
    try:
        response = requests.post(f"{base_url}/api/start-crawl", 
                               json={"url": ""},  # Empty URL should fail validation
                               headers={"Content-Type": "application/json"})
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Start crawl API working (validation): {not data['success']}")
        else:
            print(f"❌ Start crawl API failed: {response.status_code}")
    except Exception as e:
        print(f"❌ Start crawl API error: {e}")
    
    print("\n🎉 API testing completed!")

if __name__ == "__main__":
    test_api_endpoints() 