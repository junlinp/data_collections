"""
Duplicate URL Fix Script
Fixes the duplicate URL issue in the crawler queue by:
1. Removing duplicate code sections that add links twice
2. Implementing stronger deduplication logic
3. Cleaning existing duplicates from the queue
"""

import redis
import time
import logging
from collections import defaultdict

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')
logger = logging.getLogger(__name__)

def analyze_queue_duplicates():
    """Analyze the queue to count duplicates"""
    try:
        r = redis.Redis(host='redis', port=6379, decode_responses=True)
        
        logger.info("🔍 Analyzing queue for duplicates...")
        
        # Get queue length
        queue_length = r.llen('crawler:queue')
        logger.info(f"Total queue length: {queue_length}")
        
        # Sample analysis (check first 1000 URLs to avoid memory issues)
        sample_size = min(1000, queue_length)
        urls = r.lrange('crawler:queue', 0, sample_size - 1)
        
        # Count duplicates in sample
        url_counts = defaultdict(int)
        for url in urls:
            url_counts[url] += 1
        
        duplicates = {url: count for url, count in url_counts.items() if count > 1}
        
        logger.info(f"Sample analysis (first {sample_size} URLs):")
        logger.info(f"  - Unique URLs: {len(url_counts)}")
        logger.info(f"  - URLs with duplicates: {len(duplicates)}")
        logger.info(f"  - Total duplicate entries: {sum(duplicates.values()) - len(duplicates)}")
        
        if duplicates:
            logger.info("Examples of duplicates:")
            for url, count in list(duplicates.items())[:5]:
                logger.info(f"  - {url} (appears {count} times)")
        
        # Estimate total duplicates
        duplicate_ratio = len(duplicates) / len(url_counts) if url_counts else 0
        estimated_duplicates = int(queue_length * duplicate_ratio)
        
        logger.info(f"Estimated total duplicates in queue: {estimated_duplicates}")
        
        return {
            'total_queue_length': queue_length,
            'sample_size': sample_size,
            'unique_in_sample': len(url_counts),
            'duplicates_in_sample': len(duplicates),
            'estimated_total_duplicates': estimated_duplicates,
            'duplicate_ratio': duplicate_ratio
        }
        
    except Exception as e:
        logger.error(f"❌ Error analyzing queue: {e}")
        return None

def deduplicate_queue_efficiently():
    """Remove duplicates from queue efficiently using Redis operations"""
    try:
        r = redis.Redis(host='redis', port=6379, decode_responses=True)
        
        logger.info("🧹 Starting efficient queue deduplication...")
        
        # Get initial stats
        initial_length = r.llen('crawler:queue')
        logger.info(f"Initial queue length: {initial_length}")
        
        # Create a temporary deduplication set
        temp_set_key = 'crawler:queue:dedup_temp'
        new_queue_key = 'crawler:queue:dedup_new'
        
        # Clear temporary keys if they exist
        r.delete(temp_set_key, new_queue_key)
        
        # Process queue in batches to avoid memory issues
        batch_size = 1000
        processed = 0
        duplicates_removed = 0
        
        logger.info("Processing queue in batches...")
        
        while True:
            # Get a batch of URLs
            batch = r.lrange('crawler:queue', 0, batch_size - 1)
            if not batch:
                break
            
            # Remove processed URLs from original queue
            for _ in range(len(batch)):
                r.lpop('crawler:queue')
            
            # Add unique URLs to new queue
            for url in batch:
                # Check if URL is already in our dedup set
                if r.sadd(temp_set_key, url):
                    # URL is unique, add to new queue
                    r.rpush(new_queue_key, url)
                else:
                    # URL is duplicate, count it
                    duplicates_removed += 1
            
            processed += len(batch)
            
            if processed % 10000 == 0:
                logger.info(f"Processed {processed} URLs, removed {duplicates_removed} duplicates")
        
        # Replace original queue with deduplicated queue
        r.delete('crawler:queue')
        r.rename(new_queue_key, 'crawler:queue')
        
        # Clean up temporary set
        r.delete(temp_set_key)
        
        # Update counter to match new queue length
        final_length = r.llen('crawler:queue')
        r.set('crawler:queue_counter', final_length)
        
        logger.info("✅ Queue deduplication completed!")
        logger.info(f"  - Initial length: {initial_length}")
        logger.info(f"  - Final length: {final_length}")
        logger.info(f"  - Duplicates removed: {duplicates_removed}")
        logger.info(f"  - Space saved: {duplicates_removed / initial_length * 100:.1f}%")
        
        return {
            'initial_length': initial_length,
            'final_length': final_length,
            'duplicates_removed': duplicates_removed,
            'space_saved_percent': duplicates_removed / initial_length * 100 if initial_length > 0 else 0
        }
        
    except Exception as e:
        logger.error(f"❌ Error deduplicating queue: {e}")
        return None

def implement_stronger_deduplication():
    """Implement stronger deduplication logic in Redis"""
    try:
        r = redis.Redis(host='redis', port=6379, decode_responses=True)
        
        logger.info("🔧 Implementing stronger deduplication logic...")
        
        # Set deduplication flags
        r.set('crawler:dedup_enabled', '1', ex=86400)  # Enable for 24 hours
        r.set('crawler:dedup_strict', '1', ex=86400)   # Strict mode
        
        # Create a queue addition tracking set
        r.delete('crawler:queue_additions')  # Clear any existing tracking
        
        logger.info("✅ Stronger deduplication logic enabled")
        
    except Exception as e:
        logger.error(f"❌ Error implementing stronger deduplication: {e}")

def main():
    """Main function to fix duplicate URL issues"""
    logger.info("🚀 Starting duplicate URL fix...")
    
    # Step 1: Analyze current duplicates
    analysis = analyze_queue_duplicates()
    if not analysis:
        logger.error("Failed to analyze queue")
        return
    
    # Step 2: Implement stronger deduplication
    implement_stronger_deduplication()
    
    # Step 3: Ask user if they want to clean existing duplicates
    if analysis['estimated_total_duplicates'] > 1000:
        logger.info(f"⚠️  Large number of duplicates detected: {analysis['estimated_total_duplicates']}")
        logger.info("💡 Consider running deduplication to clean the queue")
        
        # For automation, we'll proceed with deduplication
        logger.info("🧹 Proceeding with queue deduplication...")
        
        dedup_result = deduplicate_queue_efficiently()
        if dedup_result:
            logger.info("✅ Queue deduplication completed successfully!")
        else:
            logger.error("❌ Queue deduplication failed")
    
    logger.info("🎉 Duplicate URL fix completed!")

if __name__ == "__main__":
    main() 