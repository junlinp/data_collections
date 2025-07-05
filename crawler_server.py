"""
Crawler Server - Handles all web crawling operations
Provides REST API endpoints for the UI server to communicate with
Uses queue-based system with workers
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
from queue_manager import queue_manager
from crawler_worker_optimized import memory_optimized_worker_manager as worker_manager
import threading
import time
import os
import logging
import sys
import traceback
import psutil
import signal
from datetime import datetime
from redis_queue_manager import RedisQueueManager
from mongo_utils import get_mongo_manager

# Configure logging with more detailed format
logging.basicConfig(
    level=logging.INFO, 
    format='%(asctime)s - %(name)s - %(levelname)s - [PID:%(process)d] - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('/app/data/crawler_server.log', mode='a')
    ]
)
logger = logging.getLogger(__name__)

# Add startup logging
logger.info("="*80)
logger.info("CRAWLER SERVER STARTING UP")
logger.info(f"Python version: {sys.version}")
logger.info(f"Process ID: {os.getpid()}")
logger.info(f"Current working directory: {os.getcwd()}")
logger.info(f"Environment variables: {dict(os.environ)}")
logger.info("="*80)

def log_system_resources():
    """Log current system resource usage"""
    try:
        process = psutil.Process()
        memory_info = process.memory_info()
        cpu_percent = process.cpu_percent()
        
        logger.info(f"SYSTEM RESOURCES - Memory: {memory_info.rss / 1024 / 1024:.2f}MB, "
                   f"CPU: {cpu_percent}%, "
                   f"Threads: {process.num_threads()}, "
                   f"Open files: {process.num_fds()}")
        
        # Check memory usage against limits
        memory_mb = memory_info.rss / 1024 / 1024
        if memory_mb > 3000:  # 3GB warning threshold
            logger.warning(f"HIGH MEMORY USAGE: {memory_mb:.2f}MB (limit: 4GB)")
        
    except Exception as e:
        logger.error(f"Error logging system resources: {e}")

def setup_signal_handlers():
    """Setup signal handlers for graceful shutdown"""
    def signal_handler(signum, frame):
        logger.info(f"Received signal {signum}, initiating graceful shutdown...")
        log_system_resources()
        try:
            worker_manager.stop_workers()
            logger.info("Workers stopped successfully")
        except Exception as e:
            logger.error(f"Error stopping workers during shutdown: {e}")
        sys.exit(0)
    
    signal.signal(signal.SIGTERM, signal_handler)
    signal.signal(signal.SIGINT, signal_handler)

setup_signal_handlers()

app = Flask(__name__)
CORS(app)  # Enable CORS for cross-origin requests

# Log Flask app creation
logger.info("Flask app created successfully")

# Test database connections on startup
def test_database_connections():
    """Test database connections on startup"""
    logger.info("Testing database connections...")
    
    # Test Redis connection
    try:
        queue = RedisQueueManager(host='redis', port=6379)
        queue.r.ping()
        logger.info("✅ Redis connection successful")
    except Exception as e:
        logger.error(f"❌ Redis connection failed: {e}")
        logger.error(traceback.format_exc())
        raise
    
    # Test MongoDB connection
    try:
        mongo_manager = get_mongo_manager()
        stats = mongo_manager.get_database_stats()
        logger.info(f"✅ MongoDB connection successful - stats: {stats}")
    except Exception as e:
        logger.error(f"❌ MongoDB connection failed: {e}")
        logger.error(traceback.format_exc())
        raise

# Test connections before starting workers
try:
    test_database_connections()
    logger.info("All database connections verified successfully")
except Exception as e:
    logger.critical(f"Database connection test failed: {e}")
    sys.exit(1)

# Start workers automatically in a background thread to avoid blocking Flask startup
def start_workers_async():
    try:
        logger.info("Starting workers asynchronously...")
        log_system_resources()
        worker_manager.start_workers()
        logger.info("✅ Workers started successfully")
    except Exception as e:
        logger.error(f"❌ Error starting workers: {e}")
        logger.error(traceback.format_exc())

worker_thread = threading.Thread(target=start_workers_async, daemon=True)
worker_thread.start()
logger.info("Worker startup thread created")

# Monitor worker thread health
def monitor_worker_thread():
    """Monitor worker thread health"""
    if not worker_thread.is_alive():
        logger.error("❌ Worker thread is dead!")
        log_system_resources()
    else:
        logger.debug("✅ Worker thread is alive")

# Log system resources periodically
def log_resources_periodically():
    """Log system resources every 5 minutes"""
    while True:
        try:
            time.sleep(300)  # 5 minutes
            log_system_resources()
            monitor_worker_thread()
        except Exception as e:
            logger.error(f"Error in resource monitoring thread: {e}")

resource_monitor_thread = threading.Thread(target=log_resources_periodically, daemon=True)
resource_monitor_thread.start()
logger.info("Resource monitoring thread started")

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
    start_time = time.time()
    logger.info("🔍 Health check requested")
    
    try:
        log_system_resources()
        
        # Test Redis connection
        queue = RedisQueueManager(host='redis', port=6379)
        logger.info("Health check: Testing Redis connection...")
        queue.r.ping()
        logger.info("✅ Redis connection healthy")
        
        # Test MongoDB connection
        logger.info("Health check: Testing MongoDB connection...")
        mongo_manager = get_mongo_manager()
        stats = mongo_manager.get_database_stats()
        logger.info(f"✅ MongoDB connection healthy - stats: {stats}")
        
        # Get metrics from Redis (updated by workers)
        metrics = queue.r.hgetall('crawler:metrics')
        logger.info(f"Health check: Retrieved metrics from Redis: {metrics}")
        
        # Use fast approach for queue stats
        try:
            counter = queue.r.get(queue.counter_key)
            if counter is not None:
                queued_urls = int(counter)
            else:
                queued_urls = 1500000  # Conservative estimate
        except Exception as e:
            logger.warning(f"Error getting queue counter: {e}")
            queued_urls = 1500000  # Fallback estimate
            
        # Get actual metrics from Redis
        completed_urls = int(metrics.get('completed_urls', 0))
        failed_urls = int(metrics.get('failed_urls', 0))
        total_urls = int(metrics.get('total_urls', queued_urls))
        
        stats = {
            'total_urls': total_urls,
            'queued_urls': queued_urls,
            'pending_urls_count': queued_urls,
            'processing_urls': 0,
            'completed_urls': completed_urls,
            'failed_urls': failed_urls
        }
        
        logger.info(f"Health check: Queue stats compiled: {stats}")
        
        response = jsonify({
            'status': 'healthy',
            'service': 'crawler-server',
            'timestamp': time.time(),
            'workers_running': worker_manager.running,
            'queue_stats': stats,
            'uptime_seconds': time.time() - start_time,
            'memory_usage_mb': psutil.Process().memory_info().rss / 1024 / 1024
        })
        
        elapsed = time.time() - start_time
        logger.info(f"✅ Health check completed successfully in {elapsed:.2f}s")
        return response
        
    except Exception as e:
        elapsed = time.time() - start_time
        logger.error(f"❌ Health check failed after {elapsed:.2f}s: {e}")
        logger.error(traceback.format_exc())
        log_system_resources()
        
        return jsonify({
            'status': 'unhealthy',
            'service': 'crawler-server',
            'timestamp': time.time(),
            'error': str(e),
            'elapsed_seconds': elapsed
        }), 500

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

# Add error handler for unhandled exceptions
@app.errorhandler(Exception)
def handle_exception(e):
    """Handle unhandled exceptions"""
    logger.error(f"❌ Unhandled exception in Flask app: {e}")
    logger.error(traceback.format_exc())
    log_system_resources()
    
    return jsonify({
        'success': False,
        'error': 'Internal server error',
        'timestamp': time.time()
    }), 500

if __name__ == "__main__":
    logger.info("Starting Flask application...")
    logger.info(f"Binding to host: 0.0.0.0, port: 5001")
    
    try:
        app.run(host="0.0.0.0", port=5001, debug=False, threaded=True)
    except Exception as e:
        logger.critical(f"❌ Flask app failed to start: {e}")
        logger.critical(traceback.format_exc())
        sys.exit(1) 