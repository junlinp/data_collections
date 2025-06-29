import os
import sqlite3
import logging
from datetime import datetime
from flask import Flask, render_template_string, request, jsonify
from flask_cors import CORS
import requests

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)

# Configuration
SUMMARY_DB_PATH = os.getenv('SUMMARY_DB_PATH', '/app/data/summaries.db')
LLM_PROCESSOR_URL = os.getenv('LLM_PROCESSOR_URL', 'http://llm-processor:5003')

# HTML Template for the summary display interface
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
            gap: 15px;
            margin-bottom: 15px;
            font-size: 0.85em;
            color: #666;
        }
        
        .sentiment-badge {
            padding: 4px 8px;
            border-radius: 12px;
            font-size: 0.8em;
            font-weight: bold;
            text-transform: uppercase;
        }
        
        .sentiment-positive {
            background: #d4edda;
            color: #155724;
        }
        
        .sentiment-negative {
            background: #f8d7da;
            color: #721c24;
        }
        
        .sentiment-neutral {
            background: #e2e3e5;
            color: #383d41;
        }
        
        .summary-text {
            line-height: 1.6;
            margin-bottom: 15px;
            color: #555;
        }
        
        .key-points {
            margin-bottom: 15px;
        }
        
        .key-points h4 {
            margin-bottom: 8px;
            color: #333;
        }
        
        .key-points ul {
            list-style: none;
            padding-left: 0;
        }
        
        .key-points li {
            padding: 5px 0;
            padding-left: 20px;
            position: relative;
            color: #666;
        }
        
        .key-points li::before {
            content: '•';
            color: #667eea;
            font-weight: bold;
            position: absolute;
            left: 0;
        }
        
        .pagination {
            display: flex;
            justify-content: center;
            align-items: center;
            gap: 15px;
            margin-top: 30px;
        }
        
        .pagination button {
            background: white;
            border: 2px solid #ddd;
            padding: 10px 15px;
            border-radius: 8px;
            cursor: pointer;
            transition: all 0.2s;
        }
        
        .pagination button:hover:not(:disabled) {
            border-color: #667eea;
            background: #f8f9ff;
        }
        
        .pagination button:disabled {
            opacity: 0.5;
            cursor: not-allowed;
        }
        
        .pagination-info {
            color: white;
            font-weight: bold;
        }
        
        .loading {
            text-align: center;
            padding: 40px;
            color: white;
            font-size: 1.2em;
        }
        
        .error {
            background: #f8d7da;
            color: #721c24;
            padding: 15px;
            border-radius: 8px;
            margin-bottom: 20px;
        }
        
        .success {
            background: #d4edda;
            color: #155724;
            padding: 15px;
            border-radius: 8px;
            margin-bottom: 20px;
        }
        
        .processing-status {
            background: #fff3cd;
            color: #856404;
            padding: 15px;
            border-radius: 8px;
            margin-bottom: 20px;
        }
        
        .stat-card.model-card {
            background: linear-gradient(135deg, #28a745, #20c997);
            position: relative;
            cursor: help;
        }
        
        .stat-card.model-card:hover::after {
            content: attr(title);
            position: absolute;
            bottom: 100%;
            left: 50%;
            transform: translateX(-50%);
            background: rgba(0,0,0,0.8);
            color: white;
            padding: 8px 12px;
            border-radius: 6px;
            font-size: 0.8em;
            white-space: nowrap;
            z-index: 1000;
            margin-bottom: 5px;
        }
        
        @media (max-width: 768px) {
            .controls {
                flex-direction: column;
                align-items: stretch;
            }
            
            .stats {
                justify-content: center;
            }
            
            .search-box {
                flex-direction: column;
            }
            
            .search-input {
                min-width: auto;
                width: 100%;
            }
            
            .summaries-grid {
                grid-template-columns: 1fr;
            }
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🤖 AI Content Summaries</h1>
            <p>Intelligent summaries generated by LLM processing</p>
        </div>
        
        <div id="message-container"></div>
        
        <div class="controls">
            <div class="stats">
                <div class="stat-card">
                    <span class="stat-number" id="total-summaries">0</span>
                    <span class="stat-label">Total Summaries</span>
                </div>
                <div class="stat-card">
                    <span class="stat-number" id="unprocessed-count">0</span>
                    <span class="stat-label">Unprocessed</span>
                </div>
                <div class="stat-card">
                    <span class="stat-number" id="processing-status">Idle</span>
                    <span class="stat-label">Status</span>
                </div>
                <div class="stat-card model-card" title="LLM Model">
                    <span class="stat-number" id="llm-model">-</span>
                    <span class="stat-label">LLM Model</span>
                </div>
            </div>
            
            <div class="search-box">
                <input type="text" id="search-input" class="search-input" placeholder="Search summaries...">
                <button class="btn" onclick="searchSummaries()">🔍 Search</button>
                <button class="btn" onclick="clearSearch()">🗑️ Clear</button>
            </div>
            
            <div>
                <button class="btn" onclick="processAll()" id="process-btn">🚀 Process All</button>
                <button class="btn" onclick="refreshData()">🔄 Refresh</button>
            </div>
        </div>
        
        <div id="summaries-container">
            <div class="loading">Loading summaries...</div>
        </div>
        
        <div class="pagination" id="pagination" style="display: none;">
            <button onclick="changePage(-1)" id="prev-page">← Previous</button>
            <span class="pagination-info" id="page-info">Page 1 of 1</span>
            <button onclick="changePage(1)" id="next-page">Next →</button>
        </div>
    </div>
    
    <script>
        let currentPage = 1;
        let totalPages = 1;
        let currentSearch = '';
        let refreshInterval;
        
        // Initialize
        document.addEventListener('DOMContentLoaded', function() {
            loadStatus();
            loadSummaries();
            startAutoRefresh();
        });
        
        function showMessage(message, type) {
            const container = document.getElementById('message-container');
            container.innerHTML = `<div class="${type}">${message}</div>`;
            setTimeout(() => {
                container.innerHTML = '';
            }, 5000);
        }
        
        function loadStatus() {
            fetch('/api/status')
                .then(response => response.json())
                .then(data => {
                    if (data.success) {
                        document.getElementById('total-summaries').textContent = data.data.processed_count;
                        document.getElementById('unprocessed-count').textContent = data.data.unprocessed_count;
                        
                        const statusElement = document.getElementById('processing-status');
                        if (data.data.processing_in_progress) {
                            statusElement.textContent = 'Processing';
                            statusElement.style.color = '#ffc107';
                        } else {
                            statusElement.textContent = 'Idle';
                            statusElement.style.color = '#28a745';
                        }
                        
                        // Update LLM model information
                        const modelElement = document.getElementById('llm-model');
                        if (data.data.local_llm_model) {
                            modelElement.textContent = data.data.local_llm_model;
                            modelElement.title = `LLM URL: ${data.data.local_llm_url || 'N/A'}`;
                        } else {
                            modelElement.textContent = 'Unknown';
                        }
                    }
                })
                .catch(error => console.error('Error loading status:', error));
        }
        
        function loadSummaries() {
            const params = new URLSearchParams({
                page: currentPage,
                per_page: 12,
                search: currentSearch
            });
            
            fetch(`/api/summaries?${params}`)
                .then(response => response.json())
                .then(data => {
                    if (data.success) {
                        displaySummaries(data.data.summaries);
                        updatePagination(data.data.pagination);
                    } else {
                        showMessage(data.error, 'error');
                    }
                })
                .catch(error => {
                    console.error('Error loading summaries:', error);
                    showMessage('Error loading summaries', 'error');
                });
        }
        
        function displaySummaries(summaries) {
            const container = document.getElementById('summaries-container');
            
            if (summaries.length === 0) {
                container.innerHTML = '<div class="loading">No summaries found</div>';
                return;
            }
            
            const summariesHTML = summaries.map(summary => `
                <div class="summary-card">
                    <div class="card-header">
                        <div class="card-title">${summary.title || 'No Title'}</div>
                        <a href="${summary.url}" target="_blank" class="card-url">${summary.url}</a>
                    </div>
                    
                    <div class="card-meta">
                        <span class="sentiment-badge sentiment-${summary.sentiment}">${summary.sentiment}</span>
                        <span>${summary.word_count} words</span>
                        <span>${(summary.processing_time || 0).toFixed(2)}s</span>
                        <span>${new Date(summary.created_at).toLocaleDateString()}</span>
                    </div>
                    
                    <div class="summary-text">${summary.summary}</div>
                    
                    ${summary.key_points && summary.key_points.length > 0 ? `
                        <div class="key-points">
                            <h4>Key Points:</h4>
                            <ul>
                                ${summary.key_points.map(point => `<li>${point}</li>`).join('')}
                            </ul>
                        </div>
                    ` : ''}
                </div>
            `).join('');
            
            container.innerHTML = `<div class="summaries-grid">${summariesHTML}</div>`;
        }
        
        function updatePagination(pagination) {
            currentPage = pagination.page;
            totalPages = pagination.total_pages;
            
            const paginationElement = document.getElementById('pagination');
            const pageInfo = document.getElementById('page-info');
            const prevBtn = document.getElementById('prev-page');
            const nextBtn = document.getElementById('next-page');
            
            if (totalPages > 1) {
                paginationElement.style.display = 'flex';
                pageInfo.textContent = `Page ${currentPage} of ${totalPages}`;
                prevBtn.disabled = currentPage <= 1;
                nextBtn.disabled = currentPage >= totalPages;
            } else {
                paginationElement.style.display = 'none';
            }
        }
        
        function changePage(delta) {
            const newPage = currentPage + delta;
            if (newPage >= 1 && newPage <= totalPages) {
                currentPage = newPage;
                loadSummaries();
            }
        }
        
        function searchSummaries() {
            currentSearch = document.getElementById('search-input').value.trim();
            currentPage = 1;
            loadSummaries();
        }
        
        function clearSearch() {
            document.getElementById('search-input').value = '';
            currentSearch = '';
            currentPage = 1;
            loadSummaries();
        }
        
        function processAll() {
            const btn = document.getElementById('process-btn');
            btn.disabled = true;
            btn.textContent = 'Processing...';
            
            fetch('/api/process-all', {
                method: 'POST'
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    showMessage(data.message, 'success');
                    loadStatus();
                } else {
                    showMessage(data.error, 'error');
                }
            })
            .catch(error => {
                console.error('Error processing all:', error);
                showMessage('Error starting processing', 'error');
            })
            .finally(() => {
                btn.disabled = false;
                btn.textContent = '🚀 Process All';
            });
        }
        
        function refreshData() {
            loadStatus();
            loadSummaries();
        }
        
        function startAutoRefresh() {
            refreshInterval = setInterval(() => {
                loadStatus();
            }, 5000); // Refresh status every 5 seconds
        }
        
        function stopAutoRefresh() {
            if (refreshInterval) {
                clearInterval(refreshInterval);
            }
        }
        
        // Search on Enter key
        document.getElementById('search-input').addEventListener('keypress', function(e) {
            if (e.key === 'Enter') {
                searchSummaries();
            }
        });
    </script>
</body>
</html>
"""

@app.route("/")
def index():
    """Main page"""
    return HTML_TEMPLATE

@app.route("/api/status")
def get_status():
    """Get processing status"""
    try:
        # Get status from LLM processor
        response = requests.get(f"{LLM_PROCESSOR_URL}/api/status", timeout=5)
        if response.status_code == 200:
            return response.json()
        else:
            return jsonify({
                'success': False,
                'error': 'Failed to get status from LLM processor'
            }), 500
    except Exception as e:
        logger.error(f"Error getting status: {e}")
        return jsonify({
            'success': False,
            'error': f'Error getting status: {str(e)}'
        }), 500

@app.route("/api/summaries")
def get_summaries():
    """Get summaries with search and pagination"""
    try:
        page = int(request.args.get('page', 1))
        per_page = int(request.args.get('per_page', 12))
        search = request.args.get('search', '').strip()
        
        # Build URL for LLM processor
        params = {
            'page': page,
            'per_page': per_page
        }
        
        url = f"{LLM_PROCESSOR_URL}/api/summaries"
        response = requests.get(url, params=params, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            
            # Apply search filter if provided
            if search and data['success']:
                filtered_summaries = []
                for summary in data['data']['summaries']:
                    search_text = search.lower()
                    if (search_text in summary['title'].lower() or 
                        search_text in summary['summary'].lower() or
                        search_text in summary['url'].lower()):
                        filtered_summaries.append(summary)
                
                # Update pagination for filtered results
                total_count = len(filtered_summaries)
                total_pages = (total_count + per_page - 1) // per_page
                start_idx = (page - 1) * per_page
                end_idx = start_idx + per_page
                paginated_summaries = filtered_summaries[start_idx:end_idx]
                
                data['data']['summaries'] = paginated_summaries
                data['data']['pagination'] = {
                    'page': page,
                    'per_page': per_page,
                    'total_count': total_count,
                    'total_pages': total_pages
                }
            
            return data
        else:
            return jsonify({
                'success': False,
                'error': 'Failed to get summaries from LLM processor'
            }), 500
            
    except Exception as e:
        logger.error(f"Error getting summaries: {e}")
        return jsonify({
            'success': False,
            'error': f'Error getting summaries: {str(e)}'
        }), 500

@app.route("/api/process-all", methods=["POST"])
def process_all():
    """Start processing all unprocessed URLs"""
    try:
        response = requests.post(f"{LLM_PROCESSOR_URL}/api/process-all", timeout=10)
        return response.json()
    except Exception as e:
        logger.error(f"Error starting processing: {e}")
        return jsonify({
            'success': False,
            'error': f'Error starting processing: {str(e)}'
        }), 500

@app.route("/api/health")
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'service': 'summary-display',
        'timestamp': datetime.now().isoformat()
    })

if __name__ == "__main__":
    port = int(os.environ.get('PORT', 5004))
    app.run(host='0.0.0.0', port=port, debug=False) 