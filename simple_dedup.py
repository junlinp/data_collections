"""
Simple Queue Deduplication Script
Efficiently removes remaining duplicates from the Redis queue
"""

import redis
import time

def simple_deduplicate():
    """Remove duplicates from the end of the queue efficiently"""
    r = redis.Redis(host='redis', port=6379, decode_responses=True)
    
    print("🧹 Starting simple deduplication...")
    
    # Get current queue length
    initial_length = r.llen('crawler:queue')
    print(f"Initial queue length: {initial_length}")
    
    # Process from the end in small batches
    seen_urls = set()
    batch_size = 100
    duplicates_removed = 0
    processed = 0
    
    # Use a temporary list to rebuild the queue
    temp_urls = []
    
    print("Processing queue from the end...")
    while True:
        # Get a batch from the end
        batch = r.lrange('crawler:queue', -batch_size, -1)
        if not batch:
            break
        
        # Remove the batch from queue
        for _ in range(len(batch)):
            r.rpop('crawler:queue')
        
        # Process batch in reverse order (since we got from end)
        for url in reversed(batch):
            if url not in seen_urls:
                seen_urls.add(url)
                temp_urls.append(url)
            else:
                duplicates_removed += 1
        
        processed += len(batch)
        if processed % 1000 == 0:
            print(f"Processed {processed} URLs, removed {duplicates_removed} duplicates")
    
    # Rebuild queue with unique URLs
    print("Rebuilding queue with unique URLs...")
    for url in reversed(temp_urls):  # Reverse to maintain original order
        r.rpush('crawler:queue', url)
    
    final_length = r.llen('crawler:queue')
    
    print("✅ Simple deduplication completed!")
    print(f"  - Initial length: {initial_length}")
    print(f"  - Final length: {final_length}")
    print(f"  - Duplicates removed: {duplicates_removed}")
    print(f"  - Space saved: {duplicates_removed / initial_length * 100:.1f}%")

if __name__ == "__main__":
    simple_deduplicate() 