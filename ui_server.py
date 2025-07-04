"""
UI Server - Handles the web interface and communicates with the crawler server
Provides a clean separation between UI and crawling logic
Optimized for memory efficiency with on-demand data fetching
Uses queue-based system with workers
"""

from flask import Flask, request, render_template_string, redirect, url_for, jsonify
import requests
import os
import logging
from templates import HTML_TEMPLATE
import redis
import time
import json

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

app = Flask(__name__)

# Configuration
CRAWLER_SERVER_URL = os.environ.get("CRAWLER_SERVER_URL", "http://localhost:5001")

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

@app.route("/", methods=["GET"])
def index():
    """Main page with crawling interface - optimized for memory efficiency"""
    url = request.args.get("url")
    action = request.args.get("action")
    show_queue = request.args.get("show_queue") == "true" or request.args.get("show_status") == "true"
    
    message = ""
    success = False

    if url and action == "add_to_queue":
        # Add URL to queue
        add_response = make_crawler_request("/api/add-url", method="POST", data={"url": url})
        if add_response and add_response.get('success'):
            message = f"Added {url} to queue. Workers will process it automatically."
            success = True
        else:
            message = f"Error adding URL to queue: {add_response.get('error', 'Unknown error') if add_response else 'Failed to connect to crawler server'}"
            success = False

    # Only fetch data that's actually needed based on the active tab
    queue_stats = {}
    worker_stats = {}
    pending_urls = []
    crawling_in_progress = False

    # Always get crawling status as it's lightweight
    status_response = make_crawler_request("/api/crawl-status")
    if status_response and status_response.get('success'):
        crawling_in_progress = status_response['data']['crawling_in_progress']

    # Fetch queue and worker data if status tab is active
    if show_queue:
        # Get queue stats (lightweight)
        queue_response = make_crawler_request("/api/queue-stats")
        if queue_response and queue_response.get('success'):
            queue_stats = queue_response['data']
        else:
            # Fallback to empty stats if API call fails
            queue_stats = {
                'total_urls': 0,
                'queued_urls': 0,
                'processing_urls': 0,
                'completed_urls': 0,
                'failed_urls': 0
            }

        # Get pending URLs
        pending_response = make_crawler_request("/api/pending-urls", params={"limit": 100})
        if pending_response and pending_response.get('success'):
            pending_urls = pending_response['data']
        else:
            pending_urls = []

        # Get worker stats
        worker_response = make_crawler_request("/api/worker-stats")
        if worker_response and worker_response.get('success'):
            worker_stats = worker_response['data']
        else:
            worker_stats = {}

    # Get additional Redis metrics for display
    r = redis.Redis(host="redis", port=6379, decode_responses=True)
    visited_count = r.scard("crawler:visited")

    return render_template_string(HTML_TEMPLATE, 
                                url=url,
                                message=message, 
                                success=success,
                                queue_stats=queue_stats,  # Use crawler API data
                                worker_stats=worker_stats,
                                pending_urls=pending_urls,
                                crawling_in_progress=crawling_in_progress,
                                show_queue=show_queue,
                                redis_queue_length=queue_stats.get('queued_urls', 0),
                                redis_visited_count=visited_count)

@app.route("/data")
def view_data():
    """Redirect to main page with status tab active (data functionality removed)"""
    return redirect(url_for('index', show_status='true'))

@app.route("/queue")
def view_queue():
    """Redirect to main page with status tab active"""
    return redirect(url_for('index', show_status='true'))

@app.route("/workers")
def view_workers():
    """Redirect to main page with status tab active (workers merged with queue)"""
    return redirect(url_for('index', show_status='true'))

@app.route("/html/<path:url>")
def view_html(url):
    """View HTML content for a specific URL"""
    # Decode the URL from the path
    import urllib.parse
    decoded_url = urllib.parse.unquote(url)
    
    # Get HTML content from crawler server
    response = make_crawler_request("/api/html-content", params={"url": decoded_url})
    
    if response and response.get('success'):
        html_content = response['data']['html_content']
        return f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>HTML Content for {decoded_url}</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 20px; }}
                .header {{ background: #f0f0f0; padding: 10px; margin-bottom: 20px; }}
                .content {{ border: 1px solid #ddd; padding: 20px; background: #fafafa; }}
                pre {{ white-space: pre-wrap; word-wrap: break-word; }}
            </style>
        </head>
        <body>
            <div class="header">
                <h1>HTML Content</h1>
                <p><strong>URL:</strong> {decoded_url}</p>
                <p><strong>Size:</strong> {len(html_content)} characters</p>
                <a href="/">← Back to Crawler</a>
            </div>
            <div class="content">
                <pre>{html_content}</pre>
            </div>
        </body>
        </html>
        """
    else:
        return f"HTML content not found for URL: {decoded_url}", 404

@app.route("/api/health", methods=["GET"])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'service': 'ui-server',
        'crawler_server_url': CRAWLER_SERVER_URL
    })

@app.route("/api/add-url", methods=["POST"])
def api_add_url():
    """API endpoint to add URL to queue"""
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

@app.route("/api/queue-stats", methods=["GET"])
def api_queue_stats():
    """API endpoint to get queue statistics"""
    response = make_crawler_request("/api/queue-stats")
    if response:
        return jsonify(response)
    else:
        return jsonify({'success': False, 'error': 'Failed to connect to crawler server'}), 500

@app.route("/api/worker-stats", methods=["GET"])
def api_worker_stats():
    """API endpoint to get worker statistics"""
    response = make_crawler_request("/api/worker-stats")
    if response:
        return jsonify(response)
    else:
        return jsonify({'success': False, 'error': 'Failed to connect to crawler server'}), 500

@app.route("/api/worker-timing-details", methods=["GET"])
def api_worker_timing_details():
    """API endpoint to get detailed step timing data for recent URLs"""
    try:
        r = redis.Redis(host="redis", port=6379, decode_responses=True)
        
        # Get worker IDs
        workers_data = {}
        
        # Get list of worker timing keys
        timing_keys = r.keys("crawler:metrics:worker_*:step_times")
        
        for key in timing_keys:
            worker_id = key.split(':')[2]  # Extract worker_id from key
            
            # Get recent timing records (last 20)
            timing_records = r.lrange(key, 0, 19)
            
            recent_timings = []
            for record_json in timing_records:
                try:
                    record = json.loads(record_json)
                    recent_timings.append({
                        'url': record.get('url', ''),
                        'timestamp': record.get('timestamp', 0),
                        'timings': record.get('timings', {}),
                        'error': record.get('error'),
                        'total_time': sum(record.get('timings', {}).values())
                    })
                except json.JSONDecodeError:
                    continue
            
            # Sort by timestamp (most recent first)
            recent_timings.sort(key=lambda x: x['timestamp'], reverse=True)
            
            workers_data[worker_id] = {
                'recent_timings': recent_timings[:10],  # Last 10 URLs
                'total_records': len(timing_records)
            }
        
        return jsonify({
            'success': True,
            'data': workers_data
        })
        
    except Exception as e:
        logger.error(f"Error getting worker timing details: {e}")
        return jsonify({
            'success': False,
            'error': f'Error getting timing details: {str(e)}'
        }), 500

@app.route("/api/pending-urls", methods=["GET"])
def api_pending_urls():
    """API endpoint to get pending URLs"""
    limit = request.args.get("limit", 10)  # Default to 10 URLs for UI
    response = make_crawler_request("/api/pending-urls", params={"limit": limit})
    if response:
        return jsonify(response)
    else:
        return jsonify({'success': False, 'error': 'Failed to connect to crawler server'}), 500

@app.route("/api/start-workers", methods=["POST"])
def api_start_workers():
    """API endpoint to start workers"""
    data = request.get_json() or {}
    response = make_crawler_request("/api/start-workers", method="POST", data=data)
    if response:
        return jsonify(response)
    else:
        return jsonify({'success': False, 'error': 'Failed to connect to crawler server'}), 500

@app.route("/api/stop-workers", methods=["POST"])
def api_stop_workers():
    """API endpoint to stop workers"""
    response = make_crawler_request("/api/stop-workers", method="POST")
    if response:
        return jsonify(response)
    else:
        return jsonify({'success': False, 'error': 'Failed to connect to crawler server'}), 500

@app.route("/api/add-worker", methods=["POST"])
def api_add_worker():
    """API endpoint to add a worker"""
    response = make_crawler_request("/api/add-worker", method="POST")
    if response:
        return jsonify(response)
    else:
        return jsonify({'success': False, 'error': 'Failed to connect to crawler server'}), 500

@app.route("/api/clear-queue", methods=["POST"])
def api_clear_queue():
    """API endpoint to clear the queue"""
    response = make_crawler_request("/api/clear-queue", method="POST")
    if response:
        return jsonify(response)
    else:
        return jsonify({'success': False, 'error': 'Failed to connect to crawler server'}), 500

@app.route("/api/crawler-status", methods=["GET"])
def api_crawler_status():
    """Proxy endpoint to get crawler status"""
    response = make_crawler_request("/api/crawl-status")
    if response:
        return jsonify(response)
    else:
        return jsonify({'success': False, 'error': 'Failed to connect to crawler server'}), 500

@app.route("/api/crawled-data", methods=["GET"])
def api_crawled_data():
    """API endpoint for getting crawled data"""
    limit = request.args.get("limit", 50)
    offset = request.args.get("offset", 0)
    response = make_crawler_request("/api/crawled-data", params={"limit": limit, "offset": offset})
    if response:
        return jsonify(response)
    else:
        return jsonify({'success': False, 'error': 'Failed to connect to crawler server'}), 500

@app.route("/api/html-content", methods=["GET"])
def api_html_content():
    """API endpoint for getting HTML content for a specific URL"""
    url = request.args.get("url")
    if not url:
        return jsonify({'success': False, 'error': 'URL parameter required'}), 400
    
    response = make_crawler_request("/api/html-content", params={"url": url})
    if response:
        return jsonify(response)
    else:
        return jsonify({'success': False, 'error': 'Failed to connect to crawler server'}), 500

@app.route("/api/database-stats", methods=["GET"])
def api_database_stats():
    """API endpoint for getting database statistics"""
    response = make_crawler_request("/api/database-stats")
    if response:
        return jsonify(response)
    else:
        return jsonify({'success': False, 'error': 'Failed to connect to crawler server'}), 500

@app.route("/queue/redis-status")
def queue_redis_status():
    r = redis.Redis(host="redis", port=6379, decode_responses=True)
    queue_length = r.llen("crawler:queue")
    visited_count = r.scard("crawler:visited")
    return jsonify({
        "queue_length": queue_length,
        "visited_count": visited_count
    })

@app.route("/queue/history")
def queue_history():
    r = redis.Redis(host="redis", port=6379, decode_responses=True)
    now = int(time.time())
    data = r.zrangebyscore('queue:history', now - 24*3600, now, withscores=True)
    return jsonify([
        {'timestamp': int(ts), 'queue_length': int(length)}
        for ts, length in data
    ])

@app.route("/ui/metrics")
def ui_metrics():
    r = redis.Redis(host="redis", port=6379, decode_responses=True)
    metrics = r.hgetall("crawler:metrics")
    queue_length = r.llen("crawler:queue")
    visited_count = r.scard("crawler:visited")
    metrics['queue_length'] = queue_length
    metrics['visited_count'] = visited_count
    return jsonify(metrics)

@app.errorhandler(403)
def forbidden_error(error):
    """Handle 403 errors"""
    return render_template_string("""
        <!DOCTYPE html>
        <html>
        <head>
            <title>403 Forbidden</title>
            <style>
                body { font-family: Arial, sans-serif; text-align: center; margin-top: 50px; }
                .error { color: #d32f2f; font-size: 24px; margin-bottom: 20px; }
                .message { color: #666; margin-bottom: 30px; }
                .back-link { color: #2196f3; text-decoration: none; }
                .back-link:hover { text-decoration: underline; }
            </style>
        </head>
        <body>
            <div class="error">403 Forbidden</div>
            <div class="message">You don't have permission to access this resource.</div>
            <a href="/" class="back-link">← Back to Crawler</a>
        </body>
        </html>
    """), 403

@app.errorhandler(404)
def not_found_error(error):
    """Handle 404 errors"""
    return render_template_string("""
        <!DOCTYPE html>
        <html>
        <head>
            <title>404 Not Found</title>
            <style>
                body { font-family: Arial, sans-serif; text-align: center; margin-top: 50px; }
                .error { color: #d32f2f; font-size: 24px; margin-bottom: 20px; }
                .message { color: #666; margin-bottom: 30px; }
                .back-link { color: #2196f3; text-decoration: none; }
                .back-link:hover { text-decoration: underline; }
            </style>
        </head>
        <body>
            <div class="error">404 Not Found</div>
            <div class="message">The requested resource was not found.</div>
            <a href="/" class="back-link">← Back to Crawler</a>
        </body>
        </html>
    """), 404

@app.route("/api/<path:endpoint>", methods=["GET", "POST"])
def proxy_api(endpoint):
    """Proxy API requests to crawler server"""
    if request.method == "GET":
        response = make_crawler_request(f"/api/{endpoint}", params=request.args)
    else:
        response = make_crawler_request(f"/api/{endpoint}", method="POST", data=request.get_json())
    
    if response:
        return jsonify(response)
    else:
        return jsonify({'success': False, 'error': 'Failed to connect to crawler server'}), 500

if __name__ == "__main__":
    port = int(os.environ.get("UI_PORT", 5000))
    debug = os.environ.get("DEBUG", "False").lower() == "true"
    
    logger.info(f"Starting UI Server on port {port}")
    app.run(host="0.0.0.0", port=port, debug=debug) 