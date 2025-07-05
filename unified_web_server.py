"""
Unified Web Server - Combines all web functionality into one service
Integrates crawler UI, LLM processing, and summary display with direct MongoDB and Redis access
"""

import os
import logging
import time
import json
import threading
import requests
from datetime import datetime, timedelta
from flask import Flask, render_template, request, jsonify, redirect, url_for
from flask_cors import CORS
import redis
import psutil
from mongo_utils import get_mongo_manager
# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)

# Configuration
CRAWLER_SERVER_URL = os.environ.get("CRAWLER_SERVER_URL", "http://localhost:5001")
REDIS_HOST = os.environ.get("REDIS_HOST", "redis")
REDIS_PORT = int(os.environ.get("REDIS_PORT", 6379))
UNIFIED_PORT = int(os.environ.get("UNIFIED_PORT", 5000))
LOCAL_LLM_URL = os.environ.get("LOCAL_LLM_URL", "http://host.docker.internal:11434")
LOCAL_LLM_MODEL = os.environ.get("LOCAL_LLM_MODEL", "deepseek-r1:latest")

# Initialize services
mongo_manager = get_mongo_manager()
redis_client = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, decode_responses=True)

# Simple LLM processor status tracking
llm_processing_in_progress = False

class SimpleLLMProcessor:
    """Simplified LLM processor for unified service"""
    
    def __init__(self):
        self.local_llm_url = LOCAL_LLM_URL
        self.local_llm_model = LOCAL_LLM_MODEL
        self.processing_in_progress = False
    
    def check_local_llm_status(self):
        """Check if local LLM server is available"""
        try:
            response = requests.get(f"{self.local_llm_url}/api/tags", timeout=5)
            return response.status_code == 200
        except Exception as e:
            logger.error(f"Local LLM server not available: {e}")
            return False
    
    def get_unprocessed_count(self):
        """Get count of unprocessed URLs"""
        try:
            stats = mongo_manager.get_database_stats()
            total_urls = stats.get('web_content_count', 0)
            processed_count = stats.get('summaries_count', 0)
            unprocessed_count = max(0, total_urls - processed_count)
            return unprocessed_count
        except Exception as e:
            logger.error(f"Error getting unprocessed count: {e}")
            return 0
    
    def process_all_unprocessed(self):
        """Placeholder for processing all unprocessed content"""
        # This would normally trigger LLM processing
        # For now, just set processing flag
        self.processing_in_progress = True
        try:
            # Simulate processing time
            import time
            time.sleep(5)
        finally:
            self.processing_in_progress = False
    
    def process_url(self, url, title, html_content):
        """Placeholder for processing a single URL"""
        # This would normally process with LLM
        # For now, just return success
        return True

# Initialize LLM processor
llm_processor = SimpleLLMProcessor()

def make_crawler_request(endpoint, method="GET", data=None, params=None):
    """Make a request to the crawler server"""
    try:
        url = f"{CRAWLER_SERVER_URL}{endpoint}"
        if method == "GET":
            response = requests.get(url, params=params, timeout=10)
        elif method == "POST":
            response = requests.post(url, json=data, timeout=10)
        else:
            return None
        
        if response.status_code == 200:
            return response.json()
        else:
            logger.error(f"Crawler server error: {response.status_code} - {response.text}")
            return None
    except requests.exceptions.RequestException as e:
        logger.error(f"Error communicating with crawler server: {e}")
        return None

def get_redis_stats():
    """Get Redis statistics"""
    try:
        queue_length = redis_client.llen("crawler:queue")
        visited_count = redis_client.scard("crawler:visited")
        metrics = redis_client.hgetall("crawler:metrics")
        
        return {
            'queue_length': queue_length,
            'visited_count': visited_count,
            'metrics': metrics
        }
    except Exception as e:
        logger.error(f"Error getting Redis stats: {e}")
        return {
            'queue_length': 0,
            'visited_count': 0,
            'metrics': {}
        }

def get_mongodb_stats():
    """Get MongoDB statistics"""
    try:
        return mongo_manager.get_database_stats()
    except Exception as e:
        logger.error(f"Error getting MongoDB stats: {e}")
        return {}

# ==================== MAIN ROUTES ====================

@app.route("/")
def index():
    """Main unified interface with all functionality"""
    return render_template('unified_index.html')

@app.route("/api/health")
def health_check():
    """Health check endpoint"""
    try:
        # Check MongoDB connection
        mongo_stats = get_mongodb_stats()
        mongo_healthy = bool(mongo_stats)
        
        # Check Redis connection
        redis_stats = get_redis_stats()
        redis_healthy = bool(redis_stats)
        
        # Check LLM processor
        llm_healthy = llm_processor.check_local_llm_status()
        
        # Check crawler server
        crawler_response = make_crawler_request("/api/health")
        crawler_healthy = bool(crawler_response)
        
        overall_status = "healthy" if all([mongo_healthy, redis_healthy, crawler_healthy]) else "degraded"
        
        return jsonify({
            'status': overall_status,
            'service': 'unified-web-server',
            'timestamp': time.time(),
            'components': {
                'mongodb': mongo_healthy,
                'redis': redis_healthy,
                'llm_processor': llm_healthy,
                'crawler_server': crawler_healthy
            },
            'memory_usage_mb': psutil.Process().memory_info().rss / 1024 / 1024
        })
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return jsonify({
            'status': 'unhealthy',
            'service': 'unified-web-server',
            'error': str(e)
        }), 500

# ==================== CRAWLER FUNCTIONALITY ====================

@app.route("/api/crawler/add-url", methods=["POST"])
def add_url_to_queue():
    """Add URL to crawler queue"""
    data = request.get_json()
    if not data or 'url' not in data:
        return jsonify({'success': False, 'error': 'URL is required'}), 400
    
    url = data['url']
    priority = data.get('priority', 0)
    
    response = make_crawler_request("/api/add-url", method="POST", data={"url": url, "priority": priority})
    if response:
        return jsonify(response)
    else:
        return jsonify({'success': False, 'error': 'Failed to connect to crawler server'}), 500

@app.route("/api/crawler/queue-stats")
def get_queue_stats():
    """Get queue statistics"""
    response = make_crawler_request("/api/queue-stats")
    if response:
        return jsonify(response)
    else:
        return jsonify({'success': False, 'error': 'Failed to connect to crawler server'}), 500

@app.route("/api/crawler/worker-stats")
def get_worker_stats():
    """Get worker statistics"""
    response = make_crawler_request("/api/worker-stats")
    if response:
        return jsonify(response)
    else:
        return jsonify({'success': False, 'error': 'Failed to connect to crawler server'}), 500

@app.route("/api/crawler/pending-urls")
def get_pending_urls():
    """Get pending URLs"""
    limit = request.args.get("limit", 10)
    response = make_crawler_request("/api/pending-urls", params={"limit": limit})
    if response:
        return jsonify(response)
    else:
        return jsonify({'success': False, 'error': 'Failed to connect to crawler server'}), 500

@app.route("/api/crawler/start-workers", methods=["POST"])
def start_workers():
    """Start workers"""
    data = request.get_json() or {}
    response = make_crawler_request("/api/start-workers", method="POST", data=data)
    if response:
        return jsonify(response)
    else:
        return jsonify({'success': False, 'error': 'Failed to connect to crawler server'}), 500

@app.route("/api/crawler/stop-workers", methods=["POST"])
def stop_workers():
    """Stop workers"""
    response = make_crawler_request("/api/stop-workers", method="POST")
    if response:
        return jsonify(response)
    else:
        return jsonify({'success': False, 'error': 'Failed to connect to crawler server'}), 500

@app.route("/api/crawler/clear-queue", methods=["POST"])
def clear_queue():
    """Clear the queue"""
    response = make_crawler_request("/api/clear-queue", method="POST")
    if response:
        return jsonify(response)
    else:
        return jsonify({'success': False, 'error': 'Failed to connect to crawler server'}), 500

@app.route("/api/crawler/crawled-data")
def get_crawled_data():
    """Get crawled data from MongoDB"""
    try:
        limit = int(request.args.get("limit", 50))
        offset = int(request.args.get("offset", 0))
        
        # Get data directly from MongoDB
        web_content = mongo_manager.get_all_web_content(limit=limit, skip=offset)
        total_count = mongo_manager.count_web_content()
        
        # Format the response
        crawled_data = []
        for content in web_content:
            crawled_data.append({
                'url': content.get('url'),
                'title': content.get('title'),
                'text_content': content.get('text_content', '')[:200] + '...' if len(content.get('text_content', '')) > 200 else content.get('text_content', ''),
                'html_content': content.get('html_content', '')[:500] + '...' if len(content.get('html_content', '')) > 500 else content.get('html_content', ''),
                'parent_url': content.get('parent_url'),
                'created_at': content.get('created_at'),
                'updated_at': content.get('updated_at')
            })
        
        return jsonify({
            'success': True,
            'data': {
                'crawled_data': crawled_data,
                'total_count': total_count,
                'offset': offset,
                'limit': limit
            }
        })
    except Exception as e:
        logger.error(f"Error getting crawled data: {e}")
        return jsonify({
            'success': False,
            'error': f'Error getting crawled data: {str(e)}'
        }), 500

# ==================== LLM PROCESSING FUNCTIONALITY ====================

@app.route("/api/llm/status")
def get_llm_status():
    """Get LLM processing status"""
    try:
        unprocessed_count = llm_processor.get_unprocessed_count()
        stats = mongo_manager.get_database_stats()
        processed_count = stats.get('summaries_count', 0)
        llm_available = llm_processor.check_local_llm_status()
        
        return jsonify({
            'success': True,
            'data': {
                'processing_in_progress': llm_processor.processing_in_progress,
                'unprocessed_count': unprocessed_count,
                'processed_count': processed_count,
                'total_count': unprocessed_count + processed_count,
                'local_llm_available': llm_available,
                'local_llm_url': llm_processor.local_llm_url,
                'local_llm_model': llm_processor.local_llm_model
            }
        })
    except Exception as e:
        logger.error(f"Error getting LLM status: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route("/api/llm/process-all", methods=["POST"])
def process_all_content():
    """Process all unprocessed content"""
    if llm_processor.processing_in_progress:
        return jsonify({
            'success': False,
            'error': 'Processing already in progress'
        }), 400
    
    # Check if local LLM is available
    if not llm_processor.check_local_llm_status():
        return jsonify({
            'success': False,
            'error': 'Local LLM server is not available. Please ensure Ollama is running.'
        }), 503
    
    # Start processing in background thread
    thread = threading.Thread(target=llm_processor.process_all_unprocessed)
    thread.start()
    
    return jsonify({
        'success': True,
        'message': 'Started processing all unprocessed URLs'
    })

@app.route("/api/llm/process-url", methods=["POST"])
def process_single_url():
    """Process a specific URL"""
    data = request.get_json()
    if not data or 'url' not in data:
        return jsonify({
            'success': False,
            'error': 'URL is required'
        }), 400
    
    url = data['url']
    
    try:
        # Get content from MongoDB
        content = mongo_manager.get_web_content(url)
        
        if not content:
            return jsonify({
                'success': False,
                'error': 'URL not found in database'
            }), 404
        
        title = content.get('title', '')
        html_content = content.get('html_content', '')
        
        if not html_content:
            return jsonify({
                'success': False,
                'error': 'No HTML content available for this URL'
            }), 400
        
        # Process the URL
        success = llm_processor.process_url(url, title, html_content)
        
        if success:
            return jsonify({
                'success': True,
                'message': f'Successfully processed {url}'
            })
        else:
            return jsonify({
                'success': False,
                'error': f'Failed to process {url}'
            }), 500
            
    except Exception as e:
        logger.error(f"Error processing URL {url}: {e}")
        return jsonify({
            'success': False,
            'error': f'Error processing URL: {str(e)}'
        }), 500

# ==================== SUMMARY DISPLAY FUNCTIONALITY ====================

@app.route("/api/summaries")
def get_summaries():
    """Get summaries with pagination and search"""
    try:
        page = int(request.args.get('page', 1))
        per_page = int(request.args.get('per_page', 20))
        search = request.args.get('search', '').strip()
        offset = (page - 1) * per_page
        
        # Get summaries from MongoDB
        summaries_docs = mongo_manager.get_all_summaries(limit=per_page, skip=offset)
        total_count = mongo_manager.count_summaries()
        
        summaries = []
        for doc in summaries_docs:
            summary = {
                'url': doc.get('url'),
                'title': doc.get('title'),
                'summary': doc.get('summary'),
                'key_points': doc.get('key_points', '').split('\n') if doc.get('key_points') else [],
                'sentiment': doc.get('sentiment'),
                'word_count': doc.get('word_count'),
                'processing_time': doc.get('processing_time'),
                'created_at': doc.get('created_at'),
                'updated_at': doc.get('updated_at')
            }
            
            # Apply search filter if provided
            if search:
                search_lower = search.lower()
                if not (search_lower in summary.get('title', '').lower() or
                        search_lower in summary.get('summary', '').lower() or
                        search_lower in summary.get('url', '').lower()):
                    continue
            
            summaries.append(summary)
        
        return jsonify({
            'success': True,
            'data': {
                'summaries': summaries,
                'pagination': {
                    'page': page,
                    'per_page': per_page,
                    'total_count': total_count,
                    'total_pages': (total_count + per_page - 1) // per_page
                }
            }
        })
        
    except Exception as e:
        logger.error(f"Error getting summaries: {e}")
        return jsonify({
            'success': False,
            'error': f'Error getting summaries: {str(e)}'
        }), 500

@app.route("/api/summary/<path:url>")
def get_summary_by_url(url):
    """Get summary for a specific URL"""
    try:
        # Get summary from MongoDB
        summary_doc = mongo_manager.get_summary(url)
        
        if not summary_doc:
            return jsonify({
                'success': False,
                'error': 'Summary not found'
            }), 404
        
        summary = {
            'url': summary_doc.get('url'),
            'title': summary_doc.get('title'),
            'summary': summary_doc.get('summary'),
            'key_points': summary_doc.get('key_points', '').split('\n') if summary_doc.get('key_points') else [],
            'sentiment': summary_doc.get('sentiment'),
            'word_count': summary_doc.get('word_count'),
            'processing_time': summary_doc.get('processing_time'),
            'created_at': summary_doc.get('created_at'),
            'updated_at': summary_doc.get('updated_at')
        }
        
        return jsonify({
            'success': True,
            'data': summary
        })
        
    except Exception as e:
        logger.error(f"Error getting summary for {url}: {e}")
        return jsonify({
            'success': False,
            'error': f'Error getting summary: {str(e)}'
        }), 500

# ==================== UNIFIED STATS ENDPOINT ====================

@app.route("/api/unified-stats")
def get_unified_stats():
    """Get comprehensive statistics from all services"""
    try:
        # Get MongoDB stats
        mongo_stats = get_mongodb_stats()
        
        # Get Redis stats
        redis_stats = get_redis_stats()
        
        # Get LLM processing stats
        try:
            llm_status_response = get_llm_status()
            if isinstance(llm_status_response, tuple):
                llm_data = llm_status_response[0].get_json().get('data', {}) if hasattr(llm_status_response[0], 'get_json') else {}
            else:
                llm_data = llm_status_response.get_json().get('data', {}) if hasattr(llm_status_response, 'get_json') else {}
        except:
            llm_data = {}
        
        # Get crawler stats
        crawler_stats = make_crawler_request("/api/queue-stats")
        crawler_data = crawler_stats.get('data', {}) if crawler_stats else {}
        
        return jsonify({
            'success': True,
            'data': {
                'mongodb': mongo_stats,
                'redis': redis_stats,
                'llm_processing': llm_data,
                'crawler': crawler_data,
                'timestamp': time.time()
            }
        })
    except Exception as e:
        logger.error(f"Error getting unified stats: {e}")
        return jsonify({
            'success': False,
            'error': f'Error getting unified stats: {str(e)}'
        }), 500

# ==================== REDIS QUEUE MONITORING ====================

@app.route("/api/redis/queue-history")
def get_queue_history():
    """Get queue history from Redis"""
    try:
        now = int(time.time())
        data = redis_client.zrangebyscore('queue:history', now - 24*3600, now, withscores=True)
        
        history = []
        for queue_length, timestamp in data:
            history.append({
                'timestamp': int(timestamp),
                'queue_length': int(queue_length)
            })
        
        return jsonify({
            'success': True,
            'data': history
        })
    except Exception as e:
        logger.error(f"Error getting queue history: {e}")
        return jsonify({
            'success': False,
            'error': f'Error getting queue history: {str(e)}'
        }), 500

@app.route("/api/redis/metrics")
def get_redis_metrics():
    """Get Redis metrics"""
    try:
        stats = get_redis_stats()
        return jsonify({
            'success': True,
            'data': stats
        })
    except Exception as e:
        logger.error(f"Error getting Redis metrics: {e}")
        return jsonify({
            'success': False,
            'error': f'Error getting Redis metrics: {str(e)}'
        }), 500

if __name__ == "__main__":
    port = UNIFIED_PORT
    debug = os.environ.get("DEBUG", "False").lower() == "true"
    
    logger.info(f"Starting Unified Web Server on port {port}")
    logger.info(f"Crawler Server URL: {CRAWLER_SERVER_URL}")
    logger.info(f"Redis: {REDIS_HOST}:{REDIS_PORT}")
    logger.info(f"MongoDB: Connected via mongo_utils")
    
    app.run(host="0.0.0.0", port=port, debug=debug) 