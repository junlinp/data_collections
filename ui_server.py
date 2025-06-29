"""
UI Server - Handles the web interface and communicates with the crawler server
Provides a clean separation between UI and crawling logic
"""

from flask import Flask, request, render_template_string, redirect, url_for, jsonify
import requests
import os
import logging
from templates import HTML_TEMPLATE

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
    """Main page with crawling interface"""
    url = request.args.get("url")
    action = request.args.get("action")
    show_data = request.args.get("show_data") == "true"
    show_history = request.args.get("show_history") == "true"
    show_queue = request.args.get("show_queue") == "true"
    
    message = ""
    success = False
    crawl_results = None

    if url and action == "crawl":
        # Check if crawling is already in progress
        status_response = make_crawler_request("/api/crawl-status")
        if status_response and status_response.get('success'):
            crawling_in_progress = status_response['data']['crawling_in_progress']
            
            if not crawling_in_progress:
                # Start crawling
                start_response = make_crawler_request("/api/start-crawl", method="POST", data={"url": url})
                if start_response and start_response.get('success'):
                    message = f"Started unlimited crawling of {url}. Check the Queue Status tab for real-time progress."
                    success = True
                else:
                    message = f"Error starting crawl: {start_response.get('error', 'Unknown error') if start_response else 'Failed to connect to crawler server'}"
                    success = False
            else:
                message = "Crawling already in progress. Please wait for the current crawl to complete."
                success = False

    # Get data for display
    crawled_data = []
    url_stats = {}
    recent_urls = []
    most_visited = []
    queue_state = {}
    crawling_in_progress = False

    # Get crawled data
    data_response = make_crawler_request("/api/crawled-data")
    if data_response and data_response.get('success'):
        crawled_data = data_response['data']

    # Get URL stats
    stats_response = make_crawler_request("/api/stats")
    if stats_response and stats_response.get('success'):
        url_stats = stats_response['data']

    # Get recent URLs
    recent_response = make_crawler_request("/api/recent", params={"hours": 24, "limit": 20})
    if recent_response and recent_response.get('success'):
        recent_urls = recent_response['data']

    # Get most visited URLs
    most_visited_response = make_crawler_request("/api/most-visited", params={"limit": 10})
    if most_visited_response and most_visited_response.get('success'):
        most_visited = most_visited_response['data']

    # Get queue state
    queue_response = make_crawler_request("/api/queue-state")
    if queue_response and queue_response.get('success'):
        queue_state = queue_response['data']

    # Get crawling status
    status_response = make_crawler_request("/api/crawl-status")
    if status_response and status_response.get('success'):
        crawling_in_progress = status_response['data']['crawling_in_progress']

    return render_template_string(HTML_TEMPLATE, 
                                url=url,
                                message=message, 
                                success=success,
                                crawl_results=crawl_results,
                                crawled_data=crawled_data,
                                url_stats=url_stats,
                                recent_urls=recent_urls,
                                most_visited=most_visited,
                                queue_state=queue_state,
                                crawling_in_progress=crawling_in_progress,
                                show_data=show_data,
                                show_history=show_history,
                                show_queue=show_queue)

@app.route("/data")
def view_data():
    """Redirect to main page with data tab active"""
    return redirect(url_for('index', show_data='true'))

@app.route("/history")
def view_history():
    """Redirect to main page with history tab active"""
    return redirect(url_for('index', show_history='true'))

@app.route("/queue")
def view_queue():
    """Redirect to main page with queue tab active"""
    return redirect(url_for('index', show_queue='true'))

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

@app.route("/api/crawler-status", methods=["GET"])
def api_crawler_status():
    """Proxy endpoint to get crawler status"""
    response = make_crawler_request("/api/crawl-status")
    if response:
        return jsonify(response)
    else:
        return jsonify({
            'success': False,
            'error': 'Failed to connect to crawler server'
        }), 503

@app.route("/api/start-crawl", methods=["POST"])
def api_start_crawl():
    """Proxy endpoint to start crawling"""
    data = request.get_json()
    response = make_crawler_request("/api/start-crawl", method="POST", data=data)
    if response:
        return jsonify(response)
    else:
        return jsonify({
            'success': False,
            'error': 'Failed to connect to crawler server'
        }), 503

@app.route("/api/stop-crawl", methods=["POST"])
def api_stop_crawl():
    """Proxy endpoint to stop crawling"""
    response = make_crawler_request("/api/stop-crawl", method="POST")
    if response:
        return jsonify(response)
    else:
        return jsonify({
            'success': False,
            'error': 'Failed to connect to crawler server'
        }), 503

@app.route("/api/stats")
def api_stats():
    """Proxy endpoint for getting URL statistics"""
    response = make_crawler_request("/api/stats")
    if response:
        return jsonify(response)
    else:
        return jsonify({
            'success': False,
            'error': 'Failed to connect to crawler server'
        }), 503

@app.route("/api/recent")
def api_recent():
    """Proxy endpoint for getting recently visited URLs"""
    params = request.args.to_dict()
    response = make_crawler_request("/api/recent", params=params)
    if response:
        return jsonify(response)
    else:
        return jsonify({
            'success': False,
            'error': 'Failed to connect to crawler server'
        }), 503

@app.route("/api/most-visited")
def api_most_visited():
    """Proxy endpoint for getting most visited URLs"""
    params = request.args.to_dict()
    response = make_crawler_request("/api/most-visited", params=params)
    if response:
        return jsonify(response)
    else:
        return jsonify({
            'success': False,
            'error': 'Failed to connect to crawler server'
        }), 503

@app.route("/api/url-info")
def api_url_info():
    """Proxy endpoint for getting specific URL information"""
    params = request.args.to_dict()
    response = make_crawler_request("/api/url-info", params=params)
    if response:
        return jsonify(response)
    else:
        return jsonify({
            'success': False,
            'error': 'Failed to connect to crawler server'
        }), 503

@app.route("/api/html-content")
def api_html_content():
    """Proxy endpoint for getting HTML content for a specific URL"""
    params = request.args.to_dict()
    response = make_crawler_request("/api/html-content", params=params)
    if response:
        return jsonify(response)
    else:
        return jsonify({
            'success': False,
            'error': 'Failed to connect to crawler server'
        }), 503

@app.route("/api/queue-state")
def api_queue_state():
    """Proxy endpoint for getting queue state"""
    response = make_crawler_request("/api/queue-state")
    if response:
        return jsonify(response)
    else:
        return jsonify({
            'success': False,
            'error': 'Failed to connect to crawler server'
        }), 503

@app.route("/api/crawled-data")
def api_crawled_data():
    """Proxy endpoint for getting crawled data"""
    response = make_crawler_request("/api/crawled-data")
    if response:
        return jsonify(response)
    else:
        return jsonify({
            'success': False,
            'error': 'Failed to connect to crawler server'
        }), 503

@app.route("/api/url-details")
def api_url_details():
    """Proxy endpoint for getting detailed URL information"""
    params = request.args.to_dict()
    response = make_crawler_request("/api/url-details", params=params)
    if response:
        return jsonify(response)
    else:
        return jsonify({
            'success': False,
            'error': 'Failed to connect to crawler server'
        }), 503

@app.errorhandler(403)
def forbidden_error(error):
    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>403 Forbidden</title>
        <style>
            body {{ font-family: Arial, sans-serif; text-align: center; margin-top: 50px; }}
            .error {{ color: #d32f2f; font-size: 24px; margin-bottom: 20px; }}
            .message {{ color: #666; margin-bottom: 30px; }}
            .back-link {{ color: #2196f3; text-decoration: none; }}
            .back-link:hover {{ text-decoration: underline; }}
        </style>
    </head>
    <body>
        <div class="error">403 Forbidden</div>
        <div class="message">Access to this resource is forbidden.</div>
        <a href="/" class="back-link">← Back to Crawler</a>
    </body>
    </html>
    """, 403

@app.errorhandler(404)
def not_found_error(error):
    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>404 Not Found</title>
        <style>
            body {{ font-family: Arial, sans-serif; text-align: center; margin-top: 50px; }}
            .error {{ color: #d32f2f; font-size: 24px; margin-bottom: 20px; }}
            .message {{ color: #666; margin-bottom: 30px; }}
            .back-link {{ color: #2196f3; text-decoration: none; }}
            .back-link:hover {{ text-decoration: underline; }}
        </style>
    </head>
    <body>
        <div class="error">404 Not Found</div>
        <div class="message">The requested page was not found.</div>
        <a href="/" class="back-link">← Back to Crawler</a>
    </body>
    </html>
    """, 404

@app.route("/api/<path:endpoint>", methods=["GET", "POST"])
def proxy_api(endpoint):
    """Proxy all API calls to the crawler server"""
    method = request.method
    data = request.get_json() if method == "POST" else None
    params = request.args.to_dict() if method == "GET" else None
    
    response = make_crawler_request(f"/api/{endpoint}", method=method, data=data, params=params)
    if response:
        return jsonify(response)
    else:
        return jsonify({
            'success': False,
            'error': 'Failed to connect to crawler server'
        }), 503

if __name__ == "__main__":
    port = int(os.environ.get("UI_PORT", 5000))
    debug = os.environ.get("DEBUG", "False").lower() == "true"
    
    logger.info(f"Starting UI Server on port {port}")
    logger.info(f"Crawler Server URL: {CRAWLER_SERVER_URL}")
    app.run(host="0.0.0.0", port=port, debug=debug) 