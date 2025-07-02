#!/usr/bin/env python3
"""
Simple script to add RFI China URL to the crawler queue
"""

import requests
import json

def add_url_to_queue():
    """Add RFI China URL to the crawler queue"""
    
    # URL to crawl
    url = "https://www.rfi.fr/cn/%E4%B8%AD%E5%9B%BD/"
    
    # API endpoint
    api_url = "http://localhost:5001/api/add-url"
    
    # Data to send
    data = {
        "url": url,
        "priority": 0
    }
    
    try:
        print(f"Adding URL to queue: {url}")
        
        # Make the request
        response = requests.post(
            api_url,
            json=data,
            headers={"Content-Type": "application/json"},
            timeout=10
        )
        
        if response.status_code == 200:
            result = response.json()
            if result.get('success'):
                print(f"✅ Success: {result['message']}")
                return True
            else:
                print(f"❌ Error: {result.get('error', 'Unknown error')}")
                return False
        else:
            print(f"❌ HTTP Error: {response.status_code}")
            print(f"Response: {response.text}")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Request Error: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected Error: {e}")
        return False

def check_queue_status():
    """Check the current queue status"""
    
    try:
        response = requests.get("http://localhost:5001/api/queue-stats", timeout=5)
        
        if response.status_code == 200:
            result = response.json()
            if result.get('success'):
                stats = result['data']
                print(f"\n📊 Queue Status:")
                print(f"  Pending URLs: {stats.get('pending_urls', 0)}")
                print(f"  Processing URLs: {stats.get('processing_urls', 0)}")
                print(f"  Completed URLs: {stats.get('completed_urls', 0)}")
                print(f"  Failed URLs: {stats.get('failed_urls', 0)}")
                return True
            else:
                print(f"❌ Error getting queue stats: {result.get('error', 'Unknown error')}")
                return False
        else:
            print(f"❌ HTTP Error getting queue stats: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Error checking queue status: {e}")
        return False

def check_worker_status():
    """Check the current worker status"""
    
    try:
        response = requests.get("http://localhost:5001/api/worker-stats", timeout=5)
        
        if response.status_code == 200:
            result = response.json()
            if result.get('success'):
                stats = result['data']
                print(f"\n🔧 Worker Status:")
                print(f"  Total Workers: {stats.get('total_workers', 0)}")
                print(f"  Running: {stats.get('running', False)}")
                
                workers = stats.get('workers', {})
                for worker_id, worker_info in workers.items():
                    status = "🟢 Running" if worker_info.get('running') else "🔴 Stopped"
                    processed = worker_info.get('processed_urls', 0)
                    print(f"    {worker_id}: {status} (Processed: {processed})")
                return True
            else:
                print(f"❌ Error getting worker stats: {result.get('error', 'Unknown error')}")
                return False
        else:
            print(f"❌ HTTP Error getting worker stats: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Error checking worker status: {e}")
        return False

if __name__ == "__main__":
    print("🚀 RFI China Crawler Queue Management")
    print("=" * 50)
    
    # Check current status
    print("\n1. Checking current status...")
    check_queue_status()
    check_worker_status()
    
    # Add URL to queue
    print("\n2. Adding RFI China URL to queue...")
    success = add_url_to_queue()
    
    if success:
        print("\n3. Checking updated status...")
        check_queue_status()
        check_worker_status()
        
        print("\n✅ URL has been added to the queue!")
        print("The workers will automatically process it.")
        print("You can monitor progress via the web interface at http://localhost:5002")
    else:
        print("\n❌ Failed to add URL to queue.")
        print("Please check the crawler server logs for more details.") 