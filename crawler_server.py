"""
Crawler Server - Handles all web crawling operations
Provides REST API endpoints for the UI server to communicate with
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
from crawler_logic import WebCrawler
import threading
import time
import os
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)  # Enable CORS for cross-origin requests

# Get database paths from environment variables
content_db_path = os.getenv('CONTENT_DB_PATH', '/app/data/web_crawler.db')
url_history_db_path = os.getenv('URL_HISTORY_DB_PATH', '/app/data/url_history.db')

# Initialize the web crawler with proper database paths
crawler = WebCrawler(content_db_path=content_db_path, url_history_db_path=url_history_db_path)

# Global variable to track if crawling is in progress
crawling_in_progress = False
crawl_thread = None

def crawl_website_async(url):
    """Run crawling in a separate thread"""
    global crawling_in_progress
    try:
        crawling_in_progress = True
        result = crawler.crawl_website(url)
        logger.info(f"Crawling completed: {result}")
    except Exception as e:
        logger.error(f"Crawling error: {e}")
    finally:
        crawling_in_progress = False

@app.route("/api/health", methods=["GET"])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'service': 'crawler-server',
        'timestamp': time.time()
    })

@app.route("/api/start-crawl", methods=["POST"])
def api_start_crawl():
    """API endpoint to start crawling"""
    global crawling_in_progress, crawl_thread
    
    if crawling_in_progress:
        return jsonify({
            'success': False,
            'error': 'Crawling already in progress'
        }), 400
    
    data = request.get_json()
    if not data or 'url' not in data:
        return jsonify({
            'success': False,
            'error': 'URL is required'
        }), 400
    
    url = data['url']
    
    try:
        # Start crawling in a separate thread
        crawl_thread = threading.Thread(
            target=crawl_website_async,
            args=(url,)
        )
        crawl_thread.start()
        
        return jsonify({
            'success': True,
            'message': f'Started crawling of {url}',
            'url': url
        })
    except Exception as e:
        logger.error(f"Error starting crawl: {e}")
        return jsonify({
            'success': False,
            'error': f'Error starting crawl: {str(e)}'
        }), 500

@app.route("/api/stop-crawl", methods=["POST"])
def api_stop_crawl():
    """API endpoint to stop crawling"""
    global crawling_in_progress
    
    try:
        crawler.stop_crawling()
        crawling_in_progress = False
        return jsonify({
            'success': True,
            'message': 'Crawling stopped'
        })
    except Exception as e:
        logger.error(f"Error stopping crawl: {e}")
        return jsonify({
            'success': False,
            'error': f'Error stopping crawl: {str(e)}'
        }), 500

@app.route("/api/crawl-status", methods=["GET"])
def api_crawl_status():
    """API endpoint to get crawling status"""
    global crawling_in_progress
    
    return jsonify({
        'success': True,
        'data': {
            'crawling_in_progress': crawling_in_progress,
            'queue_state': crawler.get_queue_state()
        }
    })

@app.route("/api/stats", methods=["GET"])
def api_stats():
    """API endpoint for getting URL statistics"""
    try:
        stats = crawler.get_url_history_stats()
        return jsonify({
            'success': True,
            'data': stats
        })
    except Exception as e:
        logger.error(f"Error getting stats: {e}")
        return jsonify({
            'success': False,
            'error': f'Error getting stats: {str(e)}'
        }), 500

@app.route("/api/recent", methods=["GET"])
def api_recent():
    """API endpoint for getting recently visited URLs"""
    try:
        hours = int(request.args.get("hours", 24))
        limit = int(request.args.get("limit", 20))
        recent = crawler.get_recent_urls(hours, limit)
        return jsonify({
            'success': True,
            'data': recent
        })
    except Exception as e:
        logger.error(f"Error getting recent URLs: {e}")
        return jsonify({
            'success': False,
            'error': f'Error getting recent URLs: {str(e)}'
        }), 500

@app.route("/api/most-visited", methods=["GET"])
def api_most_visited():
    """API endpoint for getting most visited URLs"""
    try:
        limit = int(request.args.get("limit", 10))
        most_visited = crawler.get_most_visited_urls(limit)
        return jsonify({
            'success': True,
            'data': most_visited
        })
    except Exception as e:
        logger.error(f"Error getting most visited URLs: {e}")
        return jsonify({
            'success': False,
            'error': f'Error getting most visited URLs: {str(e)}'
        }), 500

@app.route("/api/url-info", methods=["GET"])
def api_url_info():
    """API endpoint for getting specific URL information"""
    url = request.args.get("url")
    if not url:
        return jsonify({'success': False, 'error': 'URL parameter required'}), 400
    
    try:
        info = crawler.get_url_info(url)
        return jsonify({
            'success': True,
            'data': info
        })
    except Exception as e:
        logger.error(f"Error getting URL info: {e}")
        return jsonify({
            'success': False,
            'error': f'Error getting URL info: {str(e)}'
        }), 500

@app.route("/api/html-content", methods=["GET"])
def api_html_content():
    """API endpoint for getting HTML content for a specific URL"""
    url = request.args.get("url")
    if not url:
        return jsonify({'success': False, 'error': 'URL parameter required'}), 400
    
    try:
        html_content = crawler.get_html_content_by_url(url)
        if html_content:
            return jsonify({
                'success': True,
                'data': {
                    'url': url,
                    'html_content': html_content,
                    'size': len(html_content)
                }
            })
        else:
            return jsonify({
                'success': False,
                'error': 'HTML content not found for this URL'
            }), 404
    except Exception as e:
        logger.error(f"Error getting HTML content: {e}")
        return jsonify({
            'success': False,
            'error': f'Error getting HTML content: {str(e)}'
        }), 500

@app.route("/api/queue-state", methods=["GET"])
def api_queue_state():
    """API endpoint for getting queue state"""
    try:
        queue_state = crawler.get_queue_state()
        return jsonify({
            'success': True,
            'data': queue_state
        })
    except Exception as e:
        logger.error(f"Error getting queue state: {e}")
        return jsonify({
            'success': False,
            'error': f'Error getting queue state: {str(e)}'
        }), 500

@app.route("/api/crawled-data", methods=["GET"])
def api_crawled_data():
    """API endpoint for getting crawled data"""
    try:
        crawled_data = crawler.get_crawled_content_data()
        return jsonify({
            'success': True,
            'data': crawled_data
        })
    except Exception as e:
        logger.error(f"Error getting crawled data: {e}")
        return jsonify({
            'success': False,
            'error': f'Error getting crawled data: {str(e)}'
        }), 500

@app.route("/api/url-details", methods=["GET"])
def api_url_details():
    """API endpoint for getting detailed URL information"""
    url = request.args.get("url")
    if not url:
        return jsonify({'success': False, 'error': 'URL parameter required'}), 400
    
    try:
        # Get URL info
        url_info = crawler.get_url_info(url)
        
        # Get HTML content
        html_content = crawler.get_html_content_by_url(url)
        
        return jsonify({
            'success': True,
            'data': {
                'url_info': url_info,
                'html_content': html_content,
                'html_size': len(html_content) if html_content else 0
            }
        })
    except Exception as e:
        logger.error(f"Error getting URL details: {e}")
        return jsonify({
            'success': False,
            'error': f'Error getting URL details: {str(e)}'
        }), 500

if __name__ == "__main__":
    port = int(os.environ.get("CRAWLER_PORT", 5001))
    debug = os.environ.get("DEBUG", "False").lower() == "true"
    
    logger.info(f"Starting Crawler Server on port {port}")
    app.run(host="0.0.0.0", port=port, debug=debug) 