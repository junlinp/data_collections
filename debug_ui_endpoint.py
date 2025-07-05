"""
Debug UI Endpoint
Test the exact logic used in the UI endpoint
"""

import redis
import time
import json

def debug_ui_endpoint():
    """Debug the UI endpoint logic"""
    r = redis.Redis(host='redis', port=6379, decode_responses=True)
    
    print("🔍 Debugging UI endpoint logic...")
    
    # Replicate the exact UI endpoint logic
    now = int(time.time())
    print(f"Current time: {now}")
    
    data = r.zrangebyscore('queue:history', now - 24*3600, now, withscores=True)
    print(f"Raw Redis data: {data[:3]} ...")
    
    # Test the exact logic from UI endpoint
    result = [
        {'timestamp': int(timestamp), 'queue_length': int(queue_length)}
        for queue_length, timestamp in data
    ]
    
    print(f"Processed result (first 3): {result[:3]}")
    
    # Also test the opposite to see which is correct
    result_opposite = [
        {'timestamp': int(timestamp), 'queue_length': int(queue_length)}
        for timestamp, queue_length in data
    ]
    
    print(f"Opposite result (first 3): {result_opposite[:3]}")
    
    # Show which makes more sense
    if result:
        first_item = result[0]
        print(f"\nFirst result analysis:")
        print(f"Timestamp: {first_item['timestamp']} -> {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(first_item['timestamp']))}")
        print(f"Queue length: {first_item['queue_length']}")
        
    if result_opposite:
        first_opposite = result_opposite[0]
        print(f"\nOpposite result analysis:")
        print(f"Timestamp: {first_opposite['timestamp']} -> {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(first_opposite['timestamp']))}")
        print(f"Queue length: {first_opposite['queue_length']}")

if __name__ == "__main__":
    debug_ui_endpoint() 