import os
import logging
from datetime import datetime
from flask import Flask, render_template_string, request, jsonify
from flask_cors import CORS
import requests
from mongo_utils import get_mongo_manager

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)

# Configuration
SUMMARY_DB_PATH = os.getenv('SUMMARY_DB_PATH', '/app/data/summaries.db')
LLM_PROCESSOR_URL = os.getenv('LLM_PROCESSOR_URL', 'http://llm-processor:5003')

# HTML Template for the summary display interface - optimized for memory efficiency
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>AI Content Summaries</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            color: #333;
        }
        
        .container {
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
        }
        
        .header {
            text-align: center;
            margin-bottom: 30px;
            color: white;
        }
        
        .header h1 {
            font-size: 2.5em;
            margin-bottom: 10px;
            text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
        }
        
        .header p {
            font-size: 1.2em;
            opacity: 0.9;
        }
        
        .controls {
            background: white;
            padding: 20px;
            border-radius: 15px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.2);
            margin-bottom: 30px;
            display: flex;
            justify-content: space-between;
            align-items: center;
            flex-wrap: wrap;
            gap: 15px;
        }
        
        .stats {
            display: flex;
            gap: 20px;
            flex-wrap: wrap;
        }
        
        .stat-card {
            background: linear-gradient(135deg, #667eea, #764ba2);
            color: white;
            padding: 15px 20px;
            border-radius: 10px;
            text-align: center;
            min-width: 120px;
            position: relative;
        }
        
        .stat-number {
            font-size: 1.8em;
            font-weight: bold;
            display: block;
        }
        
        .stat-label {
            font-size: 0.9em;
            opacity: 0.9;
        }
        
        .stat-tooltip {
            position: absolute;
            bottom: 100%;
            left: 50%;
            transform: translateX(-50%);
            background: rgba(0,0,0,0.8);
            color: white;
            padding: 5px 10px;
            border-radius: 5px;
            font-size: 0.8em;
            white-space: nowrap;
            opacity: 0;
            pointer-events: none;
            transition: opacity 0.3s;
        }
        
        .stat-card:hover .stat-tooltip {
            opacity: 1;
        }
        
        .btn {
            background: linear-gradient(135deg, #667eea, #764ba2);
            color: white;
            border: none;
            padding: 12px 24px;
            border-radius: 8px;
            cursor: pointer;
            font-size: 1em;
            transition: transform 0.2s, box-shadow 0.2s;
            text-decoration: none;
            display: inline-block;
        }
        
        .btn:hover {
            transform: translateY(-2px);
            box-shadow: 0 5px 15px rgba(0,0,0,0.3);
        }
        
        .btn:disabled {
            opacity: 0.6;
            cursor: not-allowed;
            transform: none;
        }
        
        .btn-danger {
            background: linear-gradient(135deg, #ff6b6b, #ee5a52);
        }
        
        .search-box {
            display: flex;
            gap: 10px;
            align-items: center;
        }
        
        .search-input {
            padding: 10px 15px;
            border: 2px solid #ddd;
            border-radius: 8px;
            font-size: 1em;
            min-width: 300px;
        }
        
        .search-input:focus {
            outline: none;
            border-color: #667eea;
        }
        
        .summaries-grid {
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(400px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }
        
        .summary-card {
            background: white;
            border-radius: 15px;
            padding: 25px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.1);
            transition: transform 0.3s, box-shadow 0.3s;
            position: relative;
            overflow: hidden;
        }
        
        .summary-card:hover {
            transform: translateY(-5px);
            box-shadow: 0 20px 40px rgba(0,0,0,0.15);
        }
        
        .summary-card::before {
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            height: 4px;
            background: linear-gradient(135deg, #667eea, #764ba2);
        }
        
        .card-header {
            margin-bottom: 15px;
        }
        
        .card-title {
            font-size: 1.3em;
            font-weight: bold;
            color: #333;
            margin-bottom: 8px;
            line-height: 1.3;
        }
        
        .card-url {
            color: #667eea;
            text-decoration: none;
            font-size: 0.9em;
            word-break: break-all;
        }
        
        .card-url:hover {
            text-decoration: underline;
        }
        
        .card-meta {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 15px;
            font-size: 0.85em;
            color: #666;
        }
        
        .card-content {
            line-height: 1.6;
            color: #444;
            margin-bottom: 15px;
        }
        
        .card-tags {
            display: flex;
            flex-wrap: wrap;
            gap: 5px;
        }
        
        .tag {
            background: #e3f2fd;
            color: #1976d2;
            padding: 3px 8px;
            border-radius: 12px;
            font-size: 0.8em;
        }
        
        .loading {
            text-align: center;
            padding: 40px;
            color: white;
            font-size: 1.2em;
        }
        
        .error {
            background: #ffebee;
            color: #c62828;
            padding: 15px;
            border-radius: 8px;
            margin: 20px 0;
            border-left: 4px solid #c62828;
        }
        
        .pagination {
            display: flex;
            justify-content: center;
            gap: 10px;
            margin-top: 30px;
        }
        
        .pagination button {
            background: white;
            border: 1px solid #ddd;
            padding: 8px 12px;
            border-radius: 5px;
            cursor: pointer;
            transition: all 0.2s;
        }
        
        .pagination button:hover {
            background: #f5f5f5;
        }
        
        .pagination button.active {
            background: #667eea;
            color: white;
            border-color: #667eea;
        }
        
        .pagination button:disabled {
            opacity: 0.5;
            cursor: not-allowed;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>AI Content Summaries</h1>
            <p>Intelligent summaries of crawled web content</p>
        </div>
        
        <div class="controls">
            <div class="stats">
                <div class="stat-card" title="Total summaries">
                    <span class="stat-number" id="total-summaries">-</span>
                    <span class="stat-label">Summaries</span>
                    <div class="stat-tooltip">Total number of summaries</div>
                </div>
                <div class="stat-card" title="Processing status">
                    <span class="stat-number" id="processing-status">-</span>
                    <span class="stat-label">Status</span>
                    <div class="stat-tooltip">Current processing status</div>
                </div>
                <div class="stat-card" title="LLM Model">
                    <span class="stat-number" id="llm-model">-</span>
                    <span class="stat-label">Model</span>
                    <div class="stat-tooltip">Current LLM model being used</div>
                </div>
            </div>
            
            <div class="search-box">
                <input type="text" id="search-input" class="search-input" placeholder="Search summaries...">
                <button class="btn" onclick="searchSummaries()">Search</button>
            </div>
            
            <button class="btn" onclick="loadSummaries()">Refresh</button>
            <button class="btn btn-danger" onclick="processAllContent()">Process All</button>
        </div>
        
        <div id="summaries-container">
            <div class="loading">Loading summaries...</div>
        </div>
        
        <div class="pagination" id="pagination" style="display: none;">
            <button onclick="changePage(-1)" id="prev-btn">Previous</button>
            <span id="page-info">Page 1</span>
            <button onclick="changePage(1)" id="next-btn">Next</button>
        </div>
    </div>

    <script>
        let currentPage = 1;
        let totalPages = 1;
        let currentSearch = '';
        
        // Load initial data
        document.addEventListener('DOMContentLoaded', function() {
            loadStatus();
            loadSummaries();
        });
        
        function loadStatus() {
            fetch('/api/status')
                .then(response => response.json())
                .then(data => {
                    if (data.success) {
                        document.getElementById('total-summaries').textContent = data.data.total_summaries || 0;
                        document.getElementById('processing-status').textContent = data.data.processing_status || 'Idle';
                        document.getElementById('llm-model').textContent = data.data.llm_model || 'Unknown';
                    }
                })
                .catch(error => {
                    console.error('Error loading status:', error);
                });
        }
        
        function loadSummaries(page = 1, search = '') {
            const container = document.getElementById('summaries-container');
            container.innerHTML = '<div class="loading">Loading summaries...</div>';
            
            const params = new URLSearchParams({
                page: page,
                limit: 12
            });
            
            if (search) {
                params.append('search', search);
            }
            
            fetch(`/api/summaries?${params}`)
                .then(response => response.json())
                .then(data => {
                    if (data.success) {
                        displaySummaries(data.data.summaries);
                        updatePagination(data.data.total_pages, page);
                        currentPage = page;
                        totalPages = data.data.total_pages;
                        currentSearch = search;
                    } else {
                        container.innerHTML = `<div class="error">Error: ${data.error}</div>`;
                    }
                })
                .catch(error => {
                    console.error('Error loading summaries:', error);
                    container.innerHTML = '<div class="error">Failed to load summaries</div>';
                });
        }
        
        function displaySummaries(summaries) {
            const container = document.getElementById('summaries-container');
            
            if (summaries.length === 0) {
                container.innerHTML = '<div class="loading">No summaries found</div>';
                return;
            }
            
            const grid = document.createElement('div');
            grid.className = 'summaries-grid';
            
            summaries.forEach(summary => {
                const card = document.createElement('div');
                card.className = 'summary-card';
                
                const tags = summary.tags ? summary.tags.split(',').map(tag => tag.trim()) : [];
                const tagHtml = tags.map(tag => `<span class="tag">${tag}</span>`).join('');
                
                card.innerHTML = `
                    <div class="card-header">
                        <div class="card-title">${summary.title || 'Untitled'}</div>
                        <a href="${summary.url}" target="_blank" class="card-url">${summary.url}</a>
                    </div>
                    <div class="card-meta">
                        <span>${new Date(summary.created_at).toLocaleDateString()}</span>
                        <span>${summary.word_count || 0} words</span>
                    </div>
                    <div class="card-content">${summary.summary || 'No summary available'}</div>
                    <div class="card-tags">${tagHtml}</div>
                `;
                
                grid.appendChild(card);
            });
            
            container.innerHTML = '';
            container.appendChild(grid);
        }
        
        function updatePagination(totalPages, currentPage) {
            const pagination = document.getElementById('pagination');
            const prevBtn = document.getElementById('prev-btn');
            const nextBtn = document.getElementById('next-btn');
            const pageInfo = document.getElementById('page-info');
            
            if (totalPages <= 1) {
                pagination.style.display = 'none';
                return;
            }
            
            pagination.style.display = 'flex';
            prevBtn.disabled = currentPage <= 1;
            nextBtn.disabled = currentPage >= totalPages;
            pageInfo.textContent = `Page ${currentPage} of ${totalPages}`;
        }
        
        function changePage(delta) {
            const newPage = currentPage + delta;
            if (newPage >= 1 && newPage <= totalPages) {
                loadSummaries(newPage, currentSearch);
            }
        }
        
        function searchSummaries() {
            const searchInput = document.getElementById('search-input');
            const searchTerm = searchInput.value.trim();
            loadSummaries(1, searchTerm);
        }
        
        function processAllContent() {
            const btn = event.target;
            const originalText = btn.textContent;
            btn.textContent = 'Processing...';
            btn.disabled = true;
            
            fetch('/api/process-all', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                }
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    alert('Processing started successfully!');
                    setTimeout(() => {
                        loadStatus();
                        loadSummaries();
                    }, 2000);
                } else {
                    alert(`Error: ${data.error}`);
                }
            })
            .catch(error => {
                console.error('Error processing content:', error);
                alert('Failed to start processing');
            })
            .finally(() => {
                btn.textContent = originalText;
                btn.disabled = false;
            });
        }
        
        // Auto-refresh every 30 seconds
        setInterval(() => {
            loadStatus();
        }, 30000);
    </script>
</body>
</html>
"""

def get_mongo_manager():
    """Get MongoDB manager instance"""
    return get_mongo_manager()

def get_summaries_with_pagination(page=1, limit=12, search=''):
    """Get summaries with pagination and search from MongoDB"""
    try:
        mongo_manager = get_mongo_manager()
        offset = (page - 1) * limit
        
        # Get summaries from MongoDB
        summaries_docs = mongo_manager.get_all_summaries(limit=limit, skip=offset)
        total_count = mongo_manager.count_summaries()
        
        # Convert to expected format
        summaries = []
        for doc in summaries_docs:
            summary = {
                'url': doc.get('url'),
                'title': doc.get('title'),
                'summary': doc.get('summary'),
                'key_points': doc.get('key_points', ''),
                'sentiment': doc.get('sentiment'),
                'word_count': doc.get('word_count'),
                'processing_time': doc.get('processing_time'),
                'created_at': doc.get('created_at'),
                'updated_at': doc.get('updated_at')
            }
            summaries.append(summary)
        
        # Apply search filter if provided
        if search:
            search_lower = search.lower()
            filtered_summaries = []
            for summary in summaries:
                if (search_lower in summary.get('title', '').lower() or
                    search_lower in summary.get('summary', '').lower() or
                    search_lower in summary.get('url', '').lower()):
                    filtered_summaries.append(summary)
            summaries = filtered_summaries
            # Note: This is a simple client-side filter. For production, consider MongoDB text search
        
        return {
            'summaries': summaries,
            'total_count': total_count,
            'total_pages': (total_count + limit - 1) // limit,
            'current_page': page
        }
    except Exception as e:
        logger.error(f"Error getting summaries from MongoDB: {e}")
        return {
            'summaries': [],
            'total_count': 0,
            'total_pages': 0,
            'current_page': page
        }

def get_status_data():
    """Get status data from MongoDB and LLM processor"""
    try:
        # Get total summaries count from MongoDB
        mongo_manager = get_mongo_manager()
        stats = mongo_manager.get_database_stats()
        total_summaries = stats.get('summaries_count', 0)
        
        # Get processing status from LLM processor
        try:
            response = requests.get(f"{LLM_PROCESSOR_URL}/api/status", timeout=5)
            if response.status_code == 200:
                llm_data = response.json()
                # Map LLM processor fields to expected fields
                processing_in_progress = llm_data.get('data', {}).get('processing_in_progress', False)
                processing_status = 'Processing' if processing_in_progress else 'Idle'
                llm_model = llm_data.get('data', {}).get('local_llm_model', 'Unknown')
            else:
                processing_status = 'Error'
                llm_model = 'Unknown'
        except Exception as e:
            logger.error(f"Error connecting to LLM processor: {e}")
            processing_status = 'Offline'
            llm_model = 'Unknown'
        
        return {
            'total_summaries': total_summaries,
            'processing_status': processing_status,
            'llm_model': llm_model
        }
    except Exception as e:
        logger.error(f"Error getting status data: {e}")
        return {
            'total_summaries': 0,
            'processing_status': 'Error',
            'llm_model': 'Unknown'
        }

@app.route("/")
def index():
    """Main page - optimized for memory efficiency"""
    return render_template_string(HTML_TEMPLATE)

@app.route("/api/status")
def get_status():
    """Get system status - optimized for memory efficiency"""
    try:
        status_data = get_status_data()
        return jsonify({
            'success': True,
            'data': status_data
        })
    except Exception as e:
        logger.error(f"Error getting status: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route("/api/summaries")
def get_summaries():
    """Get summaries with pagination and search - optimized for memory efficiency"""
    try:
        page = int(request.args.get('page', 1))
        limit = int(request.args.get('limit', 12))
        search = request.args.get('search', '').strip()
        
        # Validate parameters
        if page < 1:
            page = 1
        if limit < 1 or limit > 100:
            limit = 12
        
        result = get_summaries_with_pagination(page, limit, search)
        
        return jsonify({
            'success': True,
            'data': result
        })
    except Exception as e:
        logger.error(f"Error getting summaries: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route("/api/process-all", methods=["POST"])
def process_all():
    """Process all unprocessed content - optimized for memory efficiency"""
    try:
        response = requests.post(f"{LLM_PROCESSOR_URL}/api/process-all", timeout=10)
        if response.status_code == 200:
            return jsonify(response.json())
        else:
            return jsonify({
                'success': False,
                'error': f'LLM processor returned status {response.status_code}'
            }), 500
    except Exception as e:
        logger.error(f"Error processing all content: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route("/api/health")
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'service': 'summary-display-server',
        'llm_processor_url': LLM_PROCESSOR_URL
    })

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5004, debug=False) 