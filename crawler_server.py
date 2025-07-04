"""
Crawler Server - Handles all web crawling operations
Provides REST API endpoints for the UI server to communicate with
Uses queue-based system with workers
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
from queue_manager import queue_manager
from crawler_worker import worker_manager
import threading
import time
import os
import logging
from redis_queue_manager import RedisQueueManager
from mongo_utils import get_mongo_manager

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)  # Enable CORS for cross-origin requests

# Initialize queue manager (uses Redis now)
# queue_manager.db_path is no longer needed as it uses Redis

# Initialize worker manager (uses MongoDB now)
# worker_manager.content_db_path is no longer needed as it uses MongoDB

# Start workers automatically in a background thread to avoid blocking Flask startup
def start_workers_async():
    try:
        worker_manager.start_workers()
    except Exception as e:
        logger.error(f"Error starting workers: {e}")

worker_thread = threading.Thread(target=start_workers_async, daemon=True)
worker_thread.start()

# Optionally: Start a background thread to poll Redis and process URLs
# redis_worker_status = {'running': True}
# def redis_background_worker():
#     queue = RedisQueueManager(host='redis', port=6379)
#     while True:
#         url = queue.get_next_url()
#         if url:
#             print(f"[Redis Background Worker] Processing URL: {url}")
#             # Optionally, add your processing logic here
#         else:
#             time.sleep(1)
#         # Update status
#         redis_worker_status['running'] = True
# threading.Thread(target=redis_background_worker, daemon=True).start()

@app.route("/api/ping", methods=["GET"])
def api_ping():
    return jsonify({'success': True, 'message': 'pong'})

@app.route("/api/simple-stats", methods=["GET"])
def api_simple_stats():
    """Simple stats endpoint that doesn't use Redis"""
    return jsonify({
        'success': True,
        'data': {
            'total_urls': 1000,  # Placeholder
            'queued_urls': 1000,  # Placeholder
            'processing_urls': 0,
            'completed_urls': 0,
            'failed_urls': 0
        }
    })

@app.route("/api/health", methods=["GET"])
def health_check():
    """Health check endpoint"""
    logger.info("/api/health called: start")
    queue = RedisQueueManager(host='redis', port=6379)
    logger.info("/api/health: got RedisQueueManager")
    
    # Get metrics from Redis (updated by workers)
    metrics = queue.r.hgetall('crawler:metrics')
    
    # Use fast approach for queue stats
    try:
        counter = queue.r.get(queue.counter_key)
        if counter is not None:
            queued_urls = int(counter)
        else:
            queued_urls = 1500000  # Conservative estimate
    except:
        queued_urls = 1500000  # Fallback estimate
        
    # Get actual metrics from Redis
    completed_urls = int(metrics.get('completed_urls', 0))
    failed_urls = int(metrics.get('failed_urls', 0))
    total_urls = int(metrics.get('total_urls', queued_urls))
        
    stats = {
        'total_urls': total_urls,
        'queued_urls': queued_urls,
        'pending_urls_count': queued_urls,  # Same as queued_urls for consistency
        'processing_urls': 0,  # Workers don't track this currently
        'completed_urls': completed_urls,
        'failed_urls': failed_urls
    }
    
    logger.info(f"/api/health: got queue state: {stats}")
    response = jsonify({
        'status': 'healthy',
        'service': 'crawler-server',
        'timestamp': time.time(),
        'workers_running': worker_manager.running,
        'queue_stats': stats
    })
    logger.info("/api/health: returning response")
    return response

@app.route("/api/add-url", methods=["POST"])
def api_add_url():
    """API endpoint to add URL to Redis queue"""
    data = request.get_json()
    if not data or 'url' not in data:
        return jsonify({
            'success': False,
            'error': 'URL is required'
        }), 400
    url = data['url']
    try:
        queue = RedisQueueManager(host='redis', port=6379)
        success = queue.add_url(url)
        if success:
            message = 'URL added to queue successfully'
        else:
            message = 'URL was already visited in the last 24 hours or already in queue'
        return jsonify({
            'success': success,
            'message': message,
            'url': url
        })
    except Exception as e:
        logger.error(f"Error adding URL to queue: {e}")
        return jsonify({
            'success': False,
            'error': f'Error adding URL to queue: {str(e)}'
        }), 500

@app.route("/api/queue-stats", methods=["GET"])
def api_queue_stats():
    """API endpoint to get queue statistics from Redis"""
    try:
        # Use a fast approach that doesn't hang on large queues
        queue = RedisQueueManager(host='redis', port=6379)
        
        # Get metrics from Redis (updated by workers)
        metrics = queue.r.hgetall('crawler:metrics')
        
        # Try to get a quick estimate for queue length
        try:
            # Quick check if counter exists
            counter = queue.r.get(queue.counter_key)
            if counter is not None:
                queued_urls = int(counter)
            else:
                # Use a conservative estimate for large queues
                queued_urls = 1500000  # Based on what we've seen in logs
        except:
            queued_urls = 1500000  # Fallback estimate
            
        # Get actual metrics from Redis
        completed_urls = int(metrics.get('completed_urls', 0))
        failed_urls = int(metrics.get('failed_urls', 0))
        total_urls = int(metrics.get('total_urls', queued_urls))
        
        stats = {
            'total_urls': total_urls,
            'queued_urls': queued_urls,
            'pending_urls_count': queued_urls,  # Same as queued_urls for consistency
            'processing_urls': 0,  # Workers don't track this currently
            'completed_urls': completed_urls,
            'failed_urls': failed_urls
        }
        
        return jsonify({
            'success': True,
            'data': stats
        })
    except Exception as e:
        logger.error(f"Error getting queue stats: {e}")
        return jsonify({
            'success': False,
            'error': f'Error getting queue stats: {str(e)}'
        }), 500

@app.route("/api/pending-urls", methods=["GET"])
def api_pending_urls():
    """API endpoint to get pending URLs from Redis"""
    try:
        limit = int(request.args.get("limit", 10))  # Default to 10 URLs for UI
        queue = RedisQueueManager(host='redis', port=6379)
        # Redis only stores the queue as a list, so get up to 'limit' URLs
        urls = []
        length = queue.queue_length()
        if length > 0:
            # Get up to 'limit' URLs from the left (newest)
            urls = queue.r.lrange(queue.queue_key, 0, limit-1)
        return jsonify({
            'success': True,
            'data': urls
        })
    except Exception as e:
        logger.error(f"Error getting pending URLs: {e}")
        return jsonify({
            'success': False,
            'error': f'Error getting pending URLs: {str(e)}'
        }), 500

@app.route("/api/worker-stats", methods=["GET"])
def api_worker_stats():
    """API endpoint to get worker statistics, including Redis background worker"""
    try:
        stats = worker_manager.get_worker_stats()
        # Add Redis background worker status
        # stats['redis_background_worker'] = {'running': redis_worker_status['running']}
        return jsonify({
            'success': True,
            'data': stats
        })
    except Exception as e:
        logger.error(f"Error getting worker stats: {e}")
        return jsonify({
            'success': False,
            'error': f'Error getting worker stats: {str(e)}'
        }), 500

@app.route("/api/start-workers", methods=["POST"])
def api_start_workers():
    """API endpoint to start workers"""
    try:
        data = request.get_json() or {}
        num_workers = data.get('num_workers', 2)
        
        # Update worker manager
        worker_manager.num_workers = num_workers
        worker_manager.start_workers()
        
        return jsonify({
            'success': True,
            'message': f'Started {num_workers} workers'
        })
    except Exception as e:
        logger.error(f"Error starting workers: {e}")
        return jsonify({
            'success': False,
            'error': f'Error starting workers: {str(e)}'
        }), 500

@app.route("/api/stop-workers", methods=["POST"])
def api_stop_workers():
    """API endpoint to stop workers"""
    try:
        worker_manager.stop_workers()
        return jsonify({
            'success': True,
            'message': 'Workers stopped'
        })
    except Exception as e:
        logger.error(f"Error stopping workers: {e}")
        return jsonify({
            'success': False,
            'error': f'Error stopping workers: {str(e)}'
        }), 500

@app.route("/api/add-worker", methods=["POST"])
def api_add_worker():
    """API endpoint to add a worker"""
    try:
        worker_manager.add_worker()
        return jsonify({
            'success': True,
            'message': 'Worker added'
        })
    except Exception as e:
        logger.error(f"Error adding worker: {e}")
        return jsonify({
            'success': False,
            'error': f'Error adding worker: {str(e)}'
        }), 500

@app.route("/api/clear-queue", methods=["POST"])
def api_clear_queue():
    """API endpoint to clear the queue"""
    try:
        queue_manager.clear_queue()
        return jsonify({
            'success': True,
            'message': 'Queue cleared'
        })
    except Exception as e:
        logger.error(f"Error clearing queue: {e}")
        return jsonify({
            'success': False,
            'error': f'Error clearing queue: {str(e)}'
        }), 500

# Legacy endpoints for backward compatibility
@app.route("/api/start-crawl", methods=["POST"])
def api_start_crawl():
    """Legacy endpoint - now just adds URL to queue"""
    data = request.get_json()
    if not data or 'url' not in data:
        return jsonify({
            'success': False,
            'error': 'URL is required'
        }), 400
    
    url = data['url']
    
    try:
        success, message = queue_manager.add_url_to_queue(url)
        
        if success:
            return jsonify({
                'success': True,
                'message': f'Added {url} to queue. Workers will process it automatically.',
                'url': url
            })
        else:
            return jsonify({
                'success': False,
                'error': message
            }), 400
            
    except Exception as e:
        logger.error(f"Error adding URL to queue: {e}")
        return jsonify({
            'success': False,
            'error': f'Error adding URL to queue: {str(e)}'
        }), 500

@app.route("/api/stop-crawl", methods=["POST"])
def api_stop_crawl():
    """Legacy endpoint - now stops workers"""
    try:
        worker_manager.stop_workers()
        return jsonify({
            'success': True,
            'message': 'Workers stopped'
        })
    except Exception as e:
        logger.error(f"Error stopping workers: {e}")
        return jsonify({
            'success': False,
            'error': f'Error stopping workers: {str(e)}'
        }), 500

@app.route("/api/crawl-status", methods=["GET"])
def api_crawl_status():
    """Legacy endpoint - now returns queue and worker status"""
    try:
        queue = RedisQueueManager(host='redis', port=6379)
        queue_stats = queue.get_queue_state()
        worker_stats = worker_manager.get_worker_stats()
        # Check if any workers are running
        workers_running = any(w.get('running', False) for w in worker_stats.get('workers', {}).values())
        return jsonify({
            'success': True,
            'data': {
                'crawling_in_progress': workers_running,
                'queue_state': queue_stats,
                'worker_state': worker_stats
            }
        })
    except Exception as e:
        logger.error(f"Error getting crawl status: {e}")
        return jsonify({
            'success': False,
            'error': f'Error getting crawl status: {str(e)}'
        }), 500

# Content retrieval endpoints
@app.route("/api/crawled-data", methods=["GET"])
def api_crawled_data():
    """API endpoint for getting crawled data"""
    try:
        limit = int(request.args.get("limit", 50))
        offset = int(request.args.get("offset", 0))
        
        # Get MongoDB manager
        mongo_manager = get_mongo_manager()
        
        # Get web content from MongoDB
        content_list = mongo_manager.get_all_web_content(limit=limit, skip=offset)
        
        data = []
        for content in content_list:
            text_content = content.get('text_content', '')
            data.append({
                'url': content.get('url'),
                'title': content.get('title'),
                'content': text_content[:500] + '...' if text_content and len(text_content) > 500 else text_content,
                'crawled_at': content.get('created_at'),

                'response_time': None,  # Not stored in MongoDB currently
                'content_length': len(text_content) if text_content else 0
            })
        
        return jsonify({
            'success': True,
            'data': data
        })
    except Exception as e:
        logger.error(f"Error getting crawled data: {e}")
        return jsonify({
            'success': False,
            'error': f'Error getting crawled data: {str(e)}'
        }), 500

@app.route("/api/html-content", methods=["GET"])
def api_html_content():
    """API endpoint for getting HTML content for a specific URL"""
    url = request.args.get("url")
    if not url:
        return jsonify({'success': False, 'error': 'URL parameter required'}), 400
    
    try:
        # Get MongoDB manager
        mongo_manager = get_mongo_manager()
        
        # Get web content from MongoDB
        content = mongo_manager.get_web_content(url)
        
        if content and content.get('html_content'):
            return jsonify({
                'success': True,
                'data': {
                    'html_content': content.get('html_content')
                }
            })
        else:
            return jsonify({
                'success': False,
                'error': 'HTML content not found for URL'
            }), 404
            
    except Exception as e:
        logger.error(f"Error getting HTML content: {e}")
        return jsonify({
            'success': False,
            'error': f'Error getting HTML content: {str(e)}'
        }), 500

@app.route("/api/database-stats", methods=["GET"])
def api_database_stats():
    """API endpoint for getting database statistics"""
    try:
        # Get MongoDB manager
        mongo_manager = get_mongo_manager()
        
        # Get database stats from MongoDB
        stats = mongo_manager.get_database_stats()
        
        return jsonify({
            'success': True,
            'data': {
                'content_records': stats.get('web_content_count', 0),
                'total_visits': stats.get('web_content_count', 0)  # Same as content_records for UI compatibility
            }
        })
    except Exception as e:
        logger.error(f"Error getting database stats: {e}")
        return jsonify({
            'success': False,
            'error': f'Error getting database stats: {str(e)}'
        }), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5001, debug=False) 