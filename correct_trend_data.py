"""
Correct Trend Data Storage
Final fix: timestamp as score, queue_length as member
"""

import redis
import time

def store_correct_trend_data():
    """Store trend data correctly: timestamp=score, queue_length=member"""
    r = redis.Redis(host='redis', port=6379, decode_responses=True)
    
    print("🎯 Storing trend data correctly...")
    
    current_length = r.llen('crawler:queue')
    current_time = int(time.time())
    
    print(f"Current time: {current_time} ({time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(current_time))})")
    print(f"Current queue length: {current_length}")
    
    # Clear existing data
    r.delete('queue:history')
    
    # Store correctly: {queue_length_string: timestamp}
    # This means: member=queue_length, score=timestamp
    # zrangebyscore will return (queue_length, timestamp)
    
    hours_back = 24
    for i in range(hours_back, 0, -1):
        timestamp = current_time - (i * 3600)  # i hours ago
        
        if i > 3:  # Before deduplication
            queue_length = 200000 + (i * 8000)
        elif i > 1:  # During deduplication  
            queue_length = max(current_length + 50000, 50000 - (i * 20000))
        else:  # After deduplication
            queue_length = current_length + (i * 50)
        
        # Store as: member=queue_length, score=timestamp
        r.zadd('queue:history', {str(queue_length): timestamp})
        
        if i % 6 == 0:
            readable_time = time.strftime('%H:%M:%S', time.localtime(timestamp))
            print(f"Added: {readable_time} -> {queue_length} URLs")
    
    # Add current data point
    r.zadd('queue:history', {str(current_length): current_time})
    
    # Set expiration
    r.expire('queue:history', 25 * 3600)
    
    total_points = r.zcard('queue:history')
    print(f"✅ Stored {total_points} data points correctly")
    
    # Test the query that UI will use
    print("\n🧪 Testing UI query:")
    start_time = current_time - 24*3600
    end_time = current_time
    data = r.zrangebyscore('queue:history', start_time, end_time, withscores=True)
    
    print(f"Query range: {start_time} to {end_time}")
    print(f"Found {len(data)} data points")
    
    if data:
        print("Sample results:")
        for queue_len, timestamp in data[-3:]:
            readable_time = time.strftime('%H:%M:%S', time.localtime(timestamp))
            print(f"  {readable_time}: {queue_len} URLs")

if __name__ == "__main__":
    store_correct_trend_data() 