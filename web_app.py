"""
Web application for the web crawler
Handles Flask routes and integrates with the crawling logic
"""

from flask import Flask, request, render_template_string, redirect, url_for, jsonify
from crawler_logic import WebCrawler
from templates import HTML_TEMPLATE
import threading
import time
import os

app = Flask(__name__)

# Initialize the web crawler
crawler = WebCrawler()

# Global variable to track if crawling is in progress
crawling_in_progress = False
crawl_thread = None

def crawl_website_async(url):
    """Run crawling in a separate thread"""
    global crawling_in_progress
    try:
        crawling_in_progress = True
        result = crawler.crawl_website(url)
        print("Crawling completed:", result)
    except Exception as e:
        print("Crawling error:", e)
    finally:
        crawling_in_progress = False

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

    if url and action == "crawl" and not crawling_in_progress:
        try:
            # Start crawling in a separate thread
            global crawl_thread
            crawl_thread = threading.Thread(
                target=crawl_website_async,
                args=(url,)
            )
            crawl_thread.start()
            
            message = f"Started unlimited crawling of {url}. Check the Queue Status tab for real-time progress."
            success = True
        except Exception as e:
            message = f"Error starting crawl: {str(e)}"
            success = False

    # Get data for display
    crawled_data = crawler.get_crawled_content_data()
    url_stats = crawler.get_url_history_stats()
    recent_urls = crawler.get_recent_urls(hours=24, limit=20)
    most_visited = crawler.get_most_visited_urls(limit=10)
    queue_state = crawler.get_queue_state()

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
    
    html_content = crawler.get_html_content_by_url(decoded_url)
    if html_content:
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

@app.route("/api/stats")
def api_stats():
    """API endpoint for getting URL statistics"""
    stats = crawler.get_url_history_stats()
    return jsonify({
        'success': True,
        'data': stats
    })

@app.route("/api/recent")
def api_recent():
    """API endpoint for getting recently visited URLs"""
    hours = int(request.args.get("hours", 24))
    limit = int(request.args.get("limit", 20))
    recent = crawler.get_recent_urls(hours, limit)
    return jsonify({
        'success': True,
        'data': recent
    })

@app.route("/api/most-visited")
def api_most_visited():
    """API endpoint for getting most visited URLs"""
    limit = int(request.args.get("limit", 10))
    most_visited = crawler.get_most_visited_urls(limit)
    return jsonify({
        'success': True,
        'data': most_visited
    })

@app.route("/api/url-info")
def api_url_info():
    """API endpoint for getting specific URL information"""
    url = request.args.get("url")
    if not url:
        return jsonify({'success': False, 'error': 'URL parameter required'})
    
    info = crawler.get_url_info(url)
    return jsonify({
        'success': True,
        'data': info
    })

@app.route("/api/html-content")
def api_html_content():
    """API endpoint for getting HTML content for a specific URL"""
    url = request.args.get("url")
    if not url:
        return jsonify({'success': False, 'error': 'URL parameter required'})
    
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
        })

@app.route("/api/queue-state")
def api_queue_state():
    """API endpoint for getting current queue state"""
    queue_state = crawler.get_queue_state()
    return jsonify({
        'success': True,
        'data': {
            'queue_state': queue_state,
            'crawling_in_progress': crawling_in_progress
        }
    })

@app.route("/api/crawl-status")
def api_crawl_status():
    """API endpoint for real-time crawl status"""
    global crawling_in_progress
    
    queue_state = crawler.get_queue_state()
    
    return jsonify({
        'success': True,
        'data': {
            'crawling_in_progress': crawling_in_progress,
            'queue_state': queue_state,
            'timestamp': time.time()
        }
    })

@app.route("/api/start-crawl", methods=["POST"])
def api_start_crawl():
    """API endpoint to start crawling"""
    global crawling_in_progress, crawl_thread
    
    if crawling_in_progress:
        return jsonify({
            'success': False,
            'message': 'Crawl already in progress'
        })
    
    data = request.get_json() if request.is_json else request.form
    url = data.get('url')
    
    if not url:
        return jsonify({
            'success': False,
            'message': 'URL is required'
        })
    
    try:
        # Start crawling in a separate thread
        crawl_thread = threading.Thread(
            target=crawl_website_async,
            args=(url,)
        )
        crawl_thread.start()
        
        return jsonify({
            'success': True,
            'message': f'Started crawling {url}',
            'url': url
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error starting crawl: {str(e)}'
        })

@app.route("/api/stop-crawl", methods=["POST"])
def api_stop_crawl():
    """API endpoint to stop crawling"""
    global crawling_in_progress
    
    if not crawling_in_progress:
        return jsonify({
            'success': False,
            'message': 'No crawl in progress'
        })
    
    try:
        # Request the crawler to stop
        crawler.stop_crawling()
        crawling_in_progress = False
        
        return jsonify({
            'success': True,
            'message': 'Crawl stop requested. It will stop after completing the current URL.'
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error stopping crawl: {str(e)}'
        })

@app.route("/api/crawled-data")
def api_crawled_data():
    """API endpoint for getting crawled data with pagination"""
    page = int(request.args.get("page", 1))
    per_page = int(request.args.get("per_page", 20))
    search = request.args.get("search", "")
    
    all_data = crawler.get_crawled_content_data()
    
    # Filter by search term if provided
    if search:
        all_data = [row for row in all_data if search.lower() in row[0].lower() or 
                   (row[1] and search.lower() in row[1].lower())]
    
    # Pagination
    total = len(all_data)
    start_idx = (page - 1) * per_page
    end_idx = start_idx + per_page
    paginated_data = all_data[start_idx:end_idx]
    
    return jsonify({
        'success': True,
        'data': {
            'items': paginated_data,
            'total': total,
            'page': page,
            'per_page': per_page,
            'total_pages': (total + per_page - 1) // per_page
        }
    })

@app.route("/api/url-details")
def api_url_details():
    """API endpoint for getting detailed information about a specific URL"""
    url = request.args.get("url")
    if not url:
        return jsonify({'success': False, 'error': 'URL parameter required'})
    
    # Get URL info from history
    url_info = crawler.get_url_info(url)
    
    # Get HTML content
    html_content = crawler.get_html_content_by_url(url)
    
    # Get crawled content data
    all_data = crawler.get_crawled_content_data()
    content_data = None
    for row in all_data:
        if row[0] == url:
            content_data = {
                'title': row[1],
                'content': row[2],
                'html_content': row[3],
                'links': row[4].split('\n') if row[4] else [],
                'crawled_at': row[5],
                'crawl_depth': row[6]
            }
            break
    
    return jsonify({
        'success': True,
        'data': {
            'url': url,
            'url_info': url_info,
            'content_data': content_data,
            'html_content': html_content
        }
    })

@app.errorhandler(403)
def forbidden_error(error):
    """Handle 403 Forbidden errors"""
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Access Denied - Web Crawler</title>
        <style>
            body { font-family: Arial, sans-serif; margin: 50px; text-align: center; }
            .error-container { max-width: 600px; margin: 0 auto; }
            .error-code { font-size: 72px; color: #dc3545; margin: 20px 0; }
            .error-message { font-size: 24px; color: #666; margin: 20px 0; }
            .solution { background: #f8f9fa; padding: 20px; border-radius: 5px; margin: 20px 0; }
            .button { display: inline-block; padding: 10px 20px; background: #007bff; color: white; text-decoration: none; border-radius: 5px; margin: 10px; }
        </style>
    </head>
    <body>
        <div class="error-container">
            <div class="error-code">403</div>
            <div class="error-message">Access Denied</div>
            <p>You don't have authorization to view this page.</p>
            
            <div class="solution">
                <h3>Possible Solutions:</h3>
                <ul style="text-align: left; display: inline-block;">
                    <li>Make sure the Flask application is running properly</li>
                    <li>Check if you're accessing the correct URL (http://localhost:5000)</li>
                    <li>Try refreshing the page</li>
                    <li>Check if any firewall or antivirus is blocking the connection</li>
                </ul>
            </div>
            
            <a href="/" class="button">Try Again</a>
            <a href="http://localhost:5000" class="button">Go to Homepage</a>
        </div>
    </body>
    </html>
    """, 403

@app.errorhandler(404)
def not_found_error(error):
    """Handle 404 Not Found errors"""
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Page Not Found - Web Crawler</title>
        <style>
            body { font-family: Arial, sans-serif; margin: 50px; text-align: center; }
            .error-container { max-width: 600px; margin: 0 auto; }
            .error-code { font-size: 72px; color: #ffc107; margin: 20px 0; }
            .error-message { font-size: 24px; color: #666; margin: 20px 0; }
            .button { display: inline-block; padding: 10px 20px; background: #007bff; color: white; text-decoration: none; border-radius: 5px; margin: 10px; }
        </style>
    </head>
    <body>
        <div class="error-container">
            <div class="error-code">404</div>
            <div class="error-message">Page Not Found</div>
            <p>The page you're looking for doesn't exist.</p>
            <a href="/" class="button">Go to Homepage</a>
        </div>
    </body>
    </html>
    """, 404

if __name__ == "__main__":
    # Get configuration from environment variables or use defaults
    host = os.environ.get('FLASK_HOST', '127.0.0.1')
    port = int(os.environ.get('FLASK_PORT', 5000))
    debug = os.environ.get('FLASK_DEBUG', 'True').lower() == 'true'
    
    print(f"🚀 Starting Web Crawler on http://{host}:{port}")
    print(f"📊 Debug mode: {debug}")
    print(f"🌐 Access the application at: http://localhost:{port}")
    print("Press Ctrl+C to stop the server")
    
    try:
        app.run(host=host, port=port, debug=debug, threaded=True)
    except OSError as e:
        if "Address already in use" in str(e):
            print(f"❌ Error: Port {port} is already in use.")
            print(f"💡 Try using a different port: FLASK_PORT=5001 python web_app.py")
        else:
            print(f"❌ Error starting server: {e}")
    except Exception as e:
        print(f"❌ Unexpected error: {e}") 