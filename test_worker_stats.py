#!/usr/bin/env python3
"""
Test script to query the worker stats API and check processed URL counts
"""

import requests
import json
import time

def test_worker_stats():
    """Test the worker stats API"""
    try:
        print("🔍 Testing Worker Stats API...")
        
        # Test worker stats endpoint
        response = requests.get("http://localhost:5001/api/worker-stats", timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            if data.get('success'):
                stats = data['data']
                print(f"✅ Worker stats retrieved successfully")
                print(f"Total Workers: {stats.get('total_workers', 0)}")
                print(f"Running: {stats.get('running', False)}")
                
                workers = stats.get('workers', {})
                if workers:
                    print("\n📊 Worker Details:")
                    for worker_id, worker_info in workers.items():
                        print(f"\n  Worker {worker_id}:")
                        print(f"    Status: {'🟢 Running' if worker_info.get('running') else '🔴 Stopped'}")
                        print(f"    Processed URLs: {worker_info.get('processed_urls', 0)}")
                        print(f"    Failed URLs: {worker_info.get('failed_urls', 0)}")
                        print(f"    Total URLs: {worker_info.get('total_urls', 0)}")
                        print(f"    Thread Alive: {worker_info.get('thread_alive', False)}")
                        if worker_info.get('started_at'):
                            started_at = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(float(worker_info['started_at'])))
                            print(f"    Started At: {started_at}")
                else:
                    print("❌ No workers found")
                    
                return True
            else:
                print(f"❌ API returned error: {data.get('error', 'Unknown error')}")
                return False
        else:
            print(f"❌ HTTP Error: {response.status_code}")
            print(f"Response: {response.text}")
            return False
            
    except requests.exceptions.ConnectionError:
        print("❌ Connection Error: Could not connect to crawler server")
        print("Make sure the crawler service is running on port 5001")
        return False
    except Exception as e:
        print(f"❌ Error testing worker stats: {e}")
        return False

def test_queue_stats():
    """Test the queue stats API"""
    try:
        print("\n🔍 Testing Queue Stats API...")
        
        response = requests.get("http://localhost:5001/api/queue-stats", timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            if data.get('success'):
                stats = data['data']
                print(f"✅ Queue stats retrieved successfully")
                print(f"Total URLs: {stats.get('total_urls', 0)}")
                print(f"Queued URLs: {stats.get('queued_urls', 0)}")
                print(f"Completed URLs: {stats.get('completed_urls', 0)}")
                print(f"Failed URLs: {stats.get('failed_urls', 0)}")
                return True
            else:
                print(f"❌ API returned error: {data.get('error', 'Unknown error')}")
                return False
        else:
            print(f"❌ HTTP Error: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Error testing queue stats: {e}")
        return False

def test_health_check():
    """Test the health check API"""
    try:
        print("\n🔍 Testing Health Check API...")
        
        response = requests.get("http://localhost:5001/api/health", timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Health check successful")
            print(f"Status: {data.get('status', 'Unknown')}")
            print(f"Service: {data.get('service', 'Unknown')}")
            print(f"Workers Running: {data.get('workers_running', False)}")
            
            queue_stats = data.get('queue_stats', {})
            if queue_stats:
                print(f"Queue Stats:")
                print(f"  Total URLs: {queue_stats.get('total_urls', 0)}")
                print(f"  Completed URLs: {queue_stats.get('completed_urls', 0)}")
                print(f"  Failed URLs: {queue_stats.get('failed_urls', 0)}")
            
            return True
        else:
            print(f"❌ HTTP Error: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Error testing health check: {e}")
        return False

def add_test_url():
    """Add a test URL to the queue"""
    try:
        print("\n🔍 Adding test URL to queue...")
        
        test_url = "https://httpbin.org/get"
        response = requests.post("http://localhost:5001/api/add-url", 
                               json={"url": test_url}, 
                               timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            if data.get('success'):
                print(f"✅ Test URL added successfully: {test_url}")
                return True
            else:
                print(f"❌ Failed to add URL: {data.get('error', 'Unknown error')}")
                return False
        else:
            print(f"❌ HTTP Error: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Error adding test URL: {e}")
        return False

def main():
    """Main test function"""
    print("🚀 Testing Web Crawler API Endpoints")
    print("=" * 50)
    
    # Test health check first
    health_ok = test_health_check()
    
    if health_ok:
        # Test queue stats
        test_queue_stats()
        
        # Test worker stats
        worker_ok = test_worker_stats()
        
        if worker_ok:
            # Add a test URL to see if workers process it
            add_test_url()
            
            print("\n⏳ Waiting 10 seconds for workers to process...")
            time.sleep(10)
            
            print("\n🔄 Re-checking worker stats after processing...")
            test_worker_stats()
    
    print("\n✅ API testing completed!")

if __name__ == "__main__":
    main() 