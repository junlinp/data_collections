import time
import redis

REDIS_HOST = 'redis'
REDIS_PORT = 6379
QUEUE_KEY = 'crawler:queue'
HISTORY_KEY = 'queue:history'
HISTORY_WINDOW = 24 * 3600  # 24 hours in seconds

r = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, decode_responses=True)

print('Starting Redis queue metrics tracker...')
while True:
    queue_length = r.llen(QUEUE_KEY)
    timestamp = int(time.time())
    r.zadd(HISTORY_KEY, {timestamp: queue_length})
    # Keep only last 24h of data
    r.zremrangebyscore(HISTORY_KEY, 0, timestamp - HISTORY_WINDOW)
    print(f'[{time.strftime("%Y-%m-%d %H:%M:%S")}] Queue size: {queue_length}')
    time.sleep(60) 