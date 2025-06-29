"""
HTML templates for the web crawler
Separated from the main application for better maintainability
"""

HTML_TEMPLATE = """
<!doctype html>
<html>
<head>
    <title>Advanced Web Crawler - Interactive Dashboard</title>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>
        * { box-sizing: border-box; }
        body { 
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; 
            margin: 0; 
            padding: 0; 
            background: #f5f7fa; 
            color: #333;
        }
        .container { 
            max-width: 1400px; 
            margin: 0 auto; 
            padding: 20px;
        }
        .header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 30px 0;
            margin-bottom: 30px;
            border-radius: 10px;
            text-align: center;
            box-shadow: 0 4px 15px rgba(0,0,0,0.1);
        }
        .header h1 {
            margin: 0;
            font-size: 2.5em;
            font-weight: 300;
        }
        .header p {
            margin: 10px 0 0 0;
            opacity: 0.9;
            font-size: 1.1em;
        }
        
        .form-group { margin: 20px 0; }
        input[type="text"], input[type="number"], input[type="search"] { 
            width: 100%;
            max-width: 400px;
            padding: 12px 15px; 
            font-size: 16px; 
            border: 2px solid #e1e5e9;
            border-radius: 8px;
            transition: border-color 0.3s ease;
        }
        input[type="text"]:focus, input[type="number"]:focus, input[type="search"]:focus {
            outline: none;
            border-color: #667eea;
            box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
        }
        
        button { 
            padding: 12px 24px; 
            font-size: 16px; 
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white; 
            border: none; 
            border-radius: 8px;
            cursor: pointer;
            transition: all 0.3s ease;
            font-weight: 500;
        }
        button:hover { 
            transform: translateY(-2px);
            box-shadow: 0 4px 15px rgba(102, 126, 234, 0.4);
        }
        button:disabled { 
            background: #ccc; 
            cursor: not-allowed;
            transform: none;
            box-shadow: none;
        }
        .btn-danger { 
            background: linear-gradient(135deg, #ff6b6b 0%, #ee5a52 100%);
        }
        .btn-danger:hover {
            box-shadow: 0 4px 15px rgba(255, 107, 107, 0.4);
        }
        .btn-success { 
            background: linear-gradient(135deg, #51cf66 0%, #40c057 100%);
        }
        .btn-success:hover {
            box-shadow: 0 4px 15px rgba(81, 207, 102, 0.4);
        }
        .btn-warning { 
            background: linear-gradient(135deg, #ffd43b 0%, #fcc419 100%);
            color: #212529;
        }
        .btn-warning:hover {
            box-shadow: 0 4px 15px rgba(255, 212, 59, 0.4);
        }
        
        .results { margin-top: 30px; }
        .success { 
            color: #51cf66; 
            background: #d3f9d8;
            padding: 15px;
            border-radius: 8px;
            border-left: 4px solid #51cf66;
        }
        .error { 
            color: #ff6b6b; 
            background: #ffe3e3;
            padding: 15px;
            border-radius: 8px;
            border-left: 4px solid #ff6b6b;
        }
        .info { 
            color: #339af0; 
            background: #d0ebff;
            padding: 15px;
            border-radius: 8px;
            border-left: 4px solid #339af0;
        }
        
        .data-table { 
            width: 100%; 
            border-collapse: collapse; 
            margin-top: 20px;
            background: white;
            border-radius: 10px;
            overflow: hidden;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }
        .data-table th, .data-table td { 
            border: none;
            padding: 15px; 
            text-align: left; 
        }
        .data-table th { 
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            font-weight: 500;
        }
        .data-table tr:nth-child(even) {
            background: #f8f9fa;
        }
        .data-table tr:hover {
            background: #e9ecef;
        }
        
        .content-preview { 
            max-height: 100px; 
            overflow: hidden; 
            line-height: 1.4;
        }
        
        .nav-tabs { 
            margin-bottom: 30px;
            display: flex;
            background: white;
            border-radius: 10px;
            padding: 5px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }
        .nav-tabs a { 
            padding: 15px 25px; 
            text-decoration: none; 
            color: #6c757d; 
            border-radius: 8px;
            margin: 0 5px;
            transition: all 0.3s ease;
            font-weight: 500;
        }
        .nav-tabs a:hover {
            background: #f8f9fa;
            color: #667eea;
        }
        .nav-tabs a.active { 
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            box-shadow: 0 2px 10px rgba(102, 126, 234, 0.3);
        }
        
        .crawl-settings { 
            background: white; 
            padding: 25px; 
            border-radius: 15px; 
            margin: 20px 0;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }
        .crawl-settings label { 
            display: inline-block; 
            width: 120px; 
            margin-right: 15px;
            font-weight: 500;
        }
        
        .progress { margin: 20px 0; }
        .progress-bar { 
            width: 100%; 
            background-color: #e9ecef; 
            border-radius: 10px; 
            overflow: hidden;
            height: 25px;
        }
        .progress-fill { 
            height: 100%; 
            background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
            transition: width 0.5s ease;
            border-radius: 10px;
        }
        
        .html-link { 
            color: #51cf66; 
            text-decoration: none;
            font-weight: 500;
        }
        .html-link:hover { 
            text-decoration: underline;
        }
        
        .stats-grid { 
            display: grid; 
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); 
            gap: 20px; 
            margin: 20px 0; 
        }
        .stat-card { 
            background: white; 
            padding: 25px; 
            border-radius: 15px; 
            border-left: 5px solid #667eea;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            transition: transform 0.3s ease;
        }
        .stat-card:hover {
            transform: translateY(-5px);
        }
        .stat-card h4 { 
            margin: 0 0 15px 0; 
            color: #667eea; 
            font-size: 1.2em;
        }
        .stat-card p { 
            margin: 8px 0; 
            font-size: 14px;
            color: #6c757d;
        }
        
        .queue-status { 
            background: white; 
            border: 2px solid #ffeaa7; 
            padding: 25px; 
            border-radius: 15px; 
            margin: 20px 0;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }
        .queue-status.active { 
            background: linear-gradient(135deg, #d4edda 0%, #c3e6cb 100%);
            border-color: #51cf66;
        }
        .queue-status.completed { 
            background: linear-gradient(135deg, #d1ecf1 0%, #bee5eb 100%);
            border-color: #339af0;
        }
        .queue-status.error { 
            background: linear-gradient(135deg, #f8d7da 0%, #f5c6cb 100%);
            border-color: #ff6b6b;
        }
        
        .queue-metrics { 
            display: grid; 
            grid-template-columns: repeat(auto-fit, minmax(150px, 1fr)); 
            gap: 15px; 
            margin: 20px 0; 
        }
        .metric { 
            text-align: center; 
            padding: 20px; 
            background: white; 
            border-radius: 10px;
            box-shadow: 0 2px 5px rgba(0,0,0,0.1);
        }
        .metric-value { 
            font-size: 2em; 
            font-weight: bold; 
            color: #667eea; 
            margin-bottom: 5px;
        }
        .metric-label { 
            font-size: 14px; 
            color: #6c757d;
            font-weight: 500;
        }
        
        .current-url { 
            background: #e9ecef; 
            padding: 15px; 
            border-radius: 10px; 
            margin: 15px 0;
            border-left: 4px solid #667eea;
        }
        
        .auto-refresh { 
            margin: 15px 0;
            display: flex;
            align-items: center;
            gap: 15px;
        }
        .auto-refresh input { 
            margin-right: 8px;
            transform: scale(1.2);
        }
        
        .unlimited-info { 
            background: linear-gradient(135deg, #e7f3ff 0%, #b3d9ff 100%);
            border: 2px solid #339af0; 
            padding: 25px; 
            border-radius: 15px; 
            margin: 20px 0;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }
        .unlimited-info h3 { 
            color: #0056b3; 
            margin-top: 0;
            font-size: 1.5em;
        }
        
        .single-thread-info { 
            background: linear-gradient(135deg, #fff2cc 0%, #ffeaa7 100%);
            border: 2px solid #fcc419; 
            padding: 15px; 
            border-radius: 10px; 
            margin: 15px 0;
        }
        
        .global-queue-info { 
            background: linear-gradient(135deg, #e8f5e8 0%, #c3e6cb 100%);
            border: 2px solid #51cf66; 
            padding: 25px; 
            border-radius: 15px; 
            margin: 20px 0;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }
        .global-queue-info h3 { 
            color: #155724; 
            margin-top: 0;
            font-size: 1.5em;
        }
        
        .queue-actions { 
            margin: 20px 0;
            display: flex;
            gap: 15px;
            flex-wrap: wrap;
        }
        .queue-actions button { 
            margin-right: 0;
        }
        
        .priority-high { 
            background: #ff6b6b; 
            color: white; 
            padding: 4px 8px; 
            border-radius: 5px; 
            font-size: 12px;
            font-weight: 500;
        }
        .priority-medium { 
            background: #ffd43b; 
            color: #212529; 
            padding: 4px 8px; 
            border-radius: 5px; 
            font-size: 12px;
            font-weight: 500;
        }
        .priority-low { 
            background: #6c757d; 
            color: white; 
            padding: 4px 8px; 
            border-radius: 5px; 
            font-size: 12px;
            font-weight: 500;
        }
        
        .status-pending { color: #ffd43b; font-weight: bold; }
        .status-processing { color: #667eea; font-weight: bold; }
        .status-completed { color: #51cf66; font-weight: bold; }
        .status-failed { color: #ff6b6b; font-weight: bold; }
        
        .search-box {
            margin: 20px 0;
            display: flex;
            gap: 10px;
            align-items: center;
        }
        
        .pagination {
            display: flex;
            justify-content: center;
            align-items: center;
            gap: 10px;
            margin: 20px 0;
        }
        
        .pagination button {
            padding: 8px 15px;
            font-size: 14px;
        }
        
        .loading {
            display: inline-block;
            width: 20px;
            height: 20px;
            border: 3px solid #f3f3f3;
            border-top: 3px solid #667eea;
            border-radius: 50%;
            animation: spin 1s linear infinite;
        }
        
        @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }
        
        .modal {
            display: none;
            position: fixed;
            z-index: 1000;
            left: 0;
            top: 0;
            width: 100%;
            height: 100%;
            background-color: rgba(0,0,0,0.5);
        }
        
        .modal-content {
            background-color: white;
            margin: 5% auto;
            padding: 30px;
            border-radius: 15px;
            width: 80%;
            max-width: 800px;
            max-height: 80vh;
            overflow-y: auto;
            box-shadow: 0 4px 20px rgba(0,0,0,0.3);
        }
        
        .close {
            color: #aaa;
            float: right;
            font-size: 28px;
            font-weight: bold;
            cursor: pointer;
        }
        
        .close:hover {
            color: #000;
        }
        
        .url-details {
            background: #f8f9fa;
            padding: 20px;
            border-radius: 10px;
            margin: 15px 0;
        }
        
        .url-details h4 {
            margin-top: 0;
            color: #667eea;
        }
        
        .links-list {
            max-height: 200px;
            overflow-y: auto;
            background: white;
            padding: 15px;
            border-radius: 8px;
            border: 1px solid #e9ecef;
        }
        
        .links-list a {
            display: block;
            padding: 5px 0;
            color: #667eea;
            text-decoration: none;
        }
        
        .links-list a:hover {
            text-decoration: underline;
        }
        
        @media (max-width: 768px) {
            .container { padding: 10px; }
            .header h1 { font-size: 2em; }
            .nav-tabs { flex-direction: column; }
            .nav-tabs a { margin: 2px 0; }
            .queue-metrics { grid-template-columns: repeat(2, 1fr); }
            .stats-grid { grid-template-columns: 1fr; }
            .queue-actions { flex-direction: column; }
            .modal-content { width: 95%; margin: 10% auto; }
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🚀 Advanced Web Crawler</h1>
            <p>Interactive Dashboard for Unlimited Single-Threaded Crawling</p>
        </div>
        
        <div class="single-thread-info">
            <h3>🚀 Unlimited Crawling - Single Thread</h3>
            <p><strong>No Limits:</strong> This crawler will discover and crawl ALL pages on the website without depth or page restrictions.</p>
            <p><strong>Single Thread:</strong> Simple, reliable crawling with one thread processing URLs sequentially.</p>
            <p><strong>Smart Discovery:</strong> Automatically finds and queues new URLs as they're discovered during crawling.</p>
        </div>
        
        <div class="nav-tabs">
            <a href="#crawl" class="active" onclick="showTab('crawl', event)">Crawl Website</a>
            <a href="#queue" onclick="showTab('queue', event)">Queue Status</a>
            <a href="#data" onclick="showTab('data', event)">View Saved Data</a>
            <a href="#history" onclick="showTab('history', event)">URL History</a>
        </div>
        
        <div id="crawl-tab" style="display: none;">
            <div class="crawl-settings">
                <h3>🚀 Start New Crawl</h3>
                <div class="form-group">
                    <label for="url">Website URL:</label>
                    <input name="url" id="url" type="text" placeholder="https://example.com" value="{{ url or '' }}" required>
                </div>
                <div class="single-thread-info">
                    <strong>Single-Threaded Crawling:</strong><br>
                    • <strong>Simple & Reliable:</strong> One thread processes URLs sequentially<br>
                    • <strong>No Configuration:</strong> No thread count to worry about<br>
                    • <strong>Respectful:</strong> 0.5 second delay between requests<br>
                    • <strong>Unlimited:</strong> No depth or page restrictions
                </div>
                <div class="form-group">
                    <button type="button" id="start-crawl-btn" onclick="startCrawl()" {% if crawling_in_progress %}disabled{% endif %}>
                        {% if crawling_in_progress %}
                            <span class="loading"></span> Crawling in Progress...
                        {% else %}
                            🚀 Start Unlimited Crawling
                        {% endif %}
                    </button>
                    <button type="button" id="stop-crawl-btn" onclick="stopCrawl()" class="btn-danger" style="display: none;">
                        ⏹️ Stop Crawl
                    </button>
                </div>
            </div>

            <div id="crawl-message"></div>
        </div>
        
        <div id="queue-tab" style="display: none;">
            <h2>Crawler Queue Status - Single Thread</h2>
            
            <div class="auto-refresh">
                <input type="checkbox" id="auto-refresh" checked>
                <label for="auto-refresh">Auto-refresh every 2 seconds</label>
                <button onclick="refreshQueueState()" style="margin-left: 10px;">Refresh Now</button>
                <span id="queue-tab-indicator" style="margin-left: 10px; color: #28a745; font-weight: bold; display: none;">✓ Queue Tab Active</span>
            </div>
            
            <div id="queue-status-display">
                <div class="queue-status">
                    <p>No crawl in progress. Start a new crawl to see queue status.</p>
                </div>
            </div>
        </div>
        
        <div id="data-tab" style="display: none;">
            <h2>📊 Saved Crawled Data</h2>
            
            <div class="search-box">
                <input type="search" id="data-search" placeholder="Search URLs or titles..." onkeyup="searchData()">
                <button onclick="searchData()">🔍 Search</button>
                <button onclick="clearSearch()">🗑️ Clear</button>
            </div>
            
            <div id="data-stats" class="stats-grid">
                <div class="stat-card">
                    <h4>Database Stats</h4>
                    <p><strong>Total Pages:</strong> <span id="total-pages">{{ crawled_data|length if crawled_data else 0 }}</span></p>
                    <p><strong>Data Available:</strong> Content + HTML</p>
                </div>
            </div>
            
            <div id="data-table-container">
                {% if crawled_data %}
                    <table class="data-table" id="data-table">
                        <thead>
                            <tr>
                                <th>URL</th>
                                <th>Title</th>
                                <th>Content Preview</th>
                                <th>HTML Content</th>
                                <th>Links Count</th>
                                <th>Depth</th>
                                <th>Crawled At</th>
                                <th>Actions</th>
                            </tr>
                        </thead>
                        <tbody id="data-tbody">
                        {% for row in crawled_data %}
                            <tr>
                                <td><a href="{{ row[0] }}" target="_blank">{{ row[0] }}</a></td>
                                <td>{{ row[1] or 'No title' }}</td>
                                <td class="content-preview">{{ row[2][:100] }}{% if row[2]|length > 100 %}...{% endif %}</td>
                                <td>
                                    {% if row[3] %}
                                        <a href="/html/{{ row[0] | urlencode }}" class="html-link" target="_blank">
                                            View HTML ({{ row[3]|length }} chars)
                                        </a>
                                    {% else %}
                                        <span style="color: #999;">No HTML</span>
                                    {% endif %}
                                </td>
                                <td>{{ row[4].count('\\n') + 1 if row[4] else 0 }}</td>
                                <td>{{ row[6] or 0 }}</td>
                                <td>{{ row[5] }}</td>
                                <td>
                                    <button onclick="viewUrlDetails('{{ row[0] }}')" style="padding: 5px 10px; font-size: 12px;">
                                        📋 Details
                                    </button>
                                </td>
                            </tr>
                        {% endfor %}
                        </tbody>
                    </table>
                    
                    <div class="pagination" id="data-pagination">
                        <button onclick="changePage(-1)" id="prev-page">← Previous</button>
                        <span id="page-info">Page 1 of 1</span>
                        <button onclick="changePage(1)" id="next-page">Next →</button>
                    </div>
                {% else %}
                    <p>No data has been crawled yet.</p>
                {% endif %}
            </div>
        </div>
        
        <div id="history-tab" style="display: none;">
            <h2>URL History & Statistics</h2>
            {% if url_stats %}
                <div class="stats-grid">
                    <div class="stat-card">
                        <h4>Overall Statistics</h4>
                        <p><strong>Total URLs:</strong> {{ url_stats.total_urls }}</p>
                        <p><strong>Total Domains:</strong> {{ url_stats.total_domains }}</p>
                        <p><strong>Total Visits:</strong> {{ url_stats.total_visits }}</p>
                        <p><strong>Avg Response Time:</strong> {{ "%.2f"|format(url_stats.avg_response_time or 0) }}s</p>
                    </div>
                    <div class="stat-card">
                        <h4>Time Range</h4>
                        <p><strong>Earliest Visit:</strong> {{ url_stats.earliest_visit or 'N/A' }}</p>
                        <p><strong>Latest Visit:</strong> {{ url_stats.latest_visit or 'N/A' }}</p>
                    </div>
                </div>
            {% endif %}
            
            {% if recent_urls %}
                <h3>Recently Visited URLs (Last 24 Hours)</h3>
                <table class="data-table">
                    <thead>
                        <tr>
                            <th>URL</th>
                            <th>Domain</th>
                            <th>Visit Count</th>
                            <th>Depth</th>
                            <th>Last Visited</th>
                        </tr>
                    </thead>
                    <tbody>
                    {% for url_info in recent_urls %}
                        <tr>
                            <td><a href="{{ url_info.url }}" target="_blank">{{ url_info.url }}</a></td>
                            <td>{{ url_info.domain }}</td>
                            <td>{{ url_info.visit_count }}</td>
                            <td>{{ url_info.crawl_depth }}</td>
                            <td>{{ url_info.last_visited }}</td>
                        </tr>
                    {% endfor %}
                    </tbody>
                </table>
            {% else %}
                <p>No URLs visited in the last 24 hours.</p>
            {% endif %}
            
            {% if most_visited %}
                <h3>Most Frequently Visited URLs</h3>
                <table class="data-table">
                    <thead>
                        <tr>
                            <th>URL</th>
                            <th>Domain</th>
                            <th>Visit Count</th>
                            <th>Last Visited</th>
                        </tr>
                    </thead>
                    <tbody>
                    {% for url_info in most_visited %}
                        <tr>
                            <td><a href="{{ url_info.url }}" target="_blank">{{ url_info.url }}</a></td>
                            <td>{{ url_info.domain }}</td>
                            <td>{{ url_info.visit_count }}</td>
                            <td>{{ url_info.last_visited }}</td>
                        </tr>
                    {% endfor %}
                    </tbody>
                </table>
            {% else %}
                <p>No URL history available.</p>
            {% endif %}
        </div>
    </div>
    
    <!-- URL Details Modal -->
    <div id="url-modal" class="modal">
        <div class="modal-content">
            <span class="close" onclick="closeModal()">&times;</span>
            <div id="modal-content">
                <h2>URL Details</h2>
                <div id="url-details-content">
                    <div class="loading"></div> Loading...
                </div>
            </div>
        </div>
    </div>
    
    <script>
        let refreshInterval;
        let currentPage = 1;
        let totalPages = 1;
        let currentSearch = '';
        
        function showTab(tabName, event) {
            console.log('showTab called with:', tabName, event);
            
            // Hide all tabs
            const tabs = ['crawl', 'queue', 'data', 'history'];
            tabs.forEach(tab => {
                const element = document.getElementById(tab + '-tab');
                if (element) {
                    element.style.display = 'none';
                    console.log('Hidden tab:', tab + '-tab');
                } else {
                    console.error('Tab element not found:', tab + '-tab');
                }
            });
            
            console.log('All tabs hidden');
            
            // Show selected tab
            const targetTab = document.getElementById(tabName + '-tab');
            if (targetTab) {
                targetTab.style.display = 'block';
                console.log('Showing tab:', tabName + '-tab');
                
                // Force a reflow to ensure the tab is visible
                targetTab.offsetHeight;
            } else {
                console.error('Tab not found:', tabName + '-tab');
                return;
            }
            
            // Update active tab styling - FIXED VERSION
            const navTabs = document.querySelectorAll('.nav-tabs a');
            navTabs.forEach(a => {
                a.classList.remove('active');
                console.log('Removed active class from:', a.textContent);
            });
            
            // Find and activate the correct tab
            const activeTab = document.querySelector(`.nav-tabs a[href="#${tabName}"]`);
            if (activeTab) {
                activeTab.classList.add('active');
                console.log('Added active class to:', activeTab.textContent);
            } else {
                console.error('Could not find tab link for:', tabName);
            }
            
            // Start/stop auto-refresh based on tab
            if (tabName === 'queue') {
                console.log('Queue tab selected, starting auto-refresh...');
                startAutoRefresh();
                // Show queue tab indicator
                const indicator = document.getElementById('queue-tab-indicator');
                if (indicator) {
                    indicator.style.display = 'inline';
                    console.log('Queue tab indicator shown');
                }
                // Immediately refresh queue state when switching to queue tab
                setTimeout(() => {
                    refreshQueueState();
                }, 100);
            } else {
                console.log('Non-queue tab selected, stopping auto-refresh...');
                stopAutoRefresh();
                // Hide queue tab indicator
                const indicator = document.getElementById('queue-tab-indicator');
                if (indicator) {
                    indicator.style.display = 'none';
                    console.log('Queue tab indicator hidden');
                }
            }
            
            // Additional debugging
            console.log('Tab switching completed. Current active tab:', tabName);
        }
        
        function initializeTabs() {
            console.log('Initializing tabs...');
            
            // Hide all tabs first
            const tabs = ['crawl', 'queue', 'data', 'history'];
            tabs.forEach(tab => {
                const element = document.getElementById(tab + '-tab');
                if (element) {
                    element.style.display = 'none';
                    console.log('Initialized tab as hidden:', tab + '-tab');
                } else {
                    console.error('Tab element not found during init:', tab + '-tab');
                }
            });
            
            // Check if there's data available and show data tab by default
            const totalPages = document.getElementById('total-pages');
            const hasData = totalPages && parseInt(totalPages.textContent) > 0;
            
            if (hasData) {
                // Show data tab by default if there's data
                const dataTab = document.getElementById('data-tab');
                if (dataTab) {
                    dataTab.style.display = 'block';
                    console.log('Showing data tab by default (data available)');
                }
                
                // Set the data tab as active
                const dataTabLink = document.querySelector('.nav-tabs a[href="#data"]');
                if (dataTabLink) {
                    dataTabLink.classList.add('active');
                    console.log('Set data tab as active');
                }
            } else {
                // Show crawl tab by default if no data
                const crawlTab = document.getElementById('crawl-tab');
                if (crawlTab) {
                    crawlTab.style.display = 'block';
                    console.log('Showing crawl tab by default (no data)');
                }
                
                // Set the first tab (Crawl Website) as active
                const firstTab = document.querySelector('.nav-tabs a[href="#crawl"]');
                if (firstTab) {
                    firstTab.classList.add('active');
                    console.log('Set crawl tab as active');
                }
            }
            
            // Always refresh queue state on page load to show current status
            setTimeout(() => {
                refreshQueueState();
                // If there's an active crawl, start auto-refresh
                fetch('/api/queue-state')
                    .then(response => response.json())
                    .then(data => {
                        if (data.success && data.data && (data.data.total_urls > 0 || data.data.completed_urls > 0)) {
                            // There's an active crawl, start auto-refresh
                            if (document.getElementById('auto-refresh').checked) {
                                startAutoRefresh();
                            }
                        }
                    })
                    .catch(error => console.error('Error checking queue state on init:', error));
            }, 500);
            
            console.log('Tab initialization completed');
        }
        
        function startCrawl() {
            const url = document.getElementById('url').value.trim();
            if (!url) {
                showMessage('Please enter a URL', 'error');
                return;
            }
            
            const startBtn = document.getElementById('start-crawl-btn');
            const stopBtn = document.getElementById('stop-crawl-btn');
            
            startBtn.disabled = true;
            startBtn.innerHTML = '<span class="loading"></span> Starting...';
            
            fetch('/api/start-crawl', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ url: url })
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    showMessage(data.message, 'success');
                    startBtn.style.display = 'none';
                    stopBtn.style.display = 'inline-block';
                    startAutoRefresh();
                } else {
                    showMessage(data.message, 'error');
                    startBtn.disabled = false;
                    startBtn.innerHTML = '🚀 Start Unlimited Crawling';
                }
            })
            .catch(error => {
                console.error('Error starting crawl:', error);
                showMessage('Error starting crawl', 'error');
                startBtn.disabled = false;
                startBtn.innerHTML = '🚀 Start Unlimited Crawling';
            });
        }
        
        function showMessage(message, type) {
            const messageDiv = document.getElementById('crawl-message');
            messageDiv.innerHTML = `<div class="${type}">${message}</div>`;
            setTimeout(() => {
                messageDiv.innerHTML = '';
            }, 5000);
        }
        
        function searchData() {
            const searchTerm = document.getElementById('data-search').value.trim();
            currentSearch = searchTerm;
            currentPage = 1;
            loadData();
        }
        
        function clearSearch() {
            document.getElementById('data-search').value = '';
            currentSearch = '';
            currentPage = 1;
            loadData();
        }
        
        function loadData() {
            const params = new URLSearchParams({
                page: currentPage,
                per_page: 20,
                search: currentSearch
            });
            
            fetch(`/api/crawled-data?${params}`)
                .then(response => response.json())
                .then(data => {
                    if (data.success) {
                        updateDataTable(data.data);
                    }
                })
                .catch(error => console.error('Error loading data:', error));
        }
        
        function updateDataTable(data) {
            const tbody = document.getElementById('data-tbody');
            const totalPagesSpan = document.getElementById('total-pages');
            const pageInfo = document.getElementById('page-info');
            
            totalPagesSpan.textContent = data.total;
            currentPage = data.page;
            totalPages = data.total_pages;
            pageInfo.textContent = `Page ${currentPage} of ${totalPages}`;
            
            tbody.innerHTML = data.items.map(row => `
                <tr>
                    <td><a href="${row[0]}" target="_blank">${row[0]}</a></td>
                    <td>${row[1] || 'No title'}</td>
                    <td class="content-preview">${row[2] ? (row[2].substring(0, 100) + (row[2].length > 100 ? '...' : '')) : ''}</td>
                    <td>
                        ${row[3] ? 
                            `<a href="/html/${encodeURIComponent(row[0])}" class="html-link" target="_blank">View HTML (${row[3].length} chars)</a>` :
                            '<span style="color: #999;">No HTML</span>'
                        }
                    </td>
                    <td>${row[4] ? (row[4].split('\\n').length) : 0}</td>
                    <td>${row[6] || 0}</td>
                    <td>${row[5]}</td>
                    <td>
                        <button onclick="viewUrlDetails('${row[0]}')" style="padding: 5px 10px; font-size: 12px;">
                            📋 Details
                        </button>
                    </td>
                </tr>
            `).join('');
            
            // Update pagination buttons
            document.getElementById('prev-page').disabled = currentPage <= 1;
            document.getElementById('next-page').disabled = currentPage >= totalPages;
        }
        
        function changePage(delta) {
            const newPage = currentPage + delta;
            if (newPage >= 1 && newPage <= totalPages) {
                currentPage = newPage;
                loadData();
            }
        }
        
        function viewUrlDetails(url) {
            const modal = document.getElementById('url-modal');
            const content = document.getElementById('url-details-content');
            
            modal.style.display = 'block';
            content.innerHTML = '<div class="loading"></div> Loading...';
            
            fetch(`/api/url-details?url=${encodeURIComponent(url)}`)
                .then(response => response.json())
                .then(data => {
                    if (data.success) {
                        const urlData = data.data;
                        content.innerHTML = `
                            <div class="url-details">
                                <h4>URL Information</h4>
                                <p><strong>URL:</strong> <a href="${urlData.url}" target="_blank">${urlData.url}</a></p>
                                ${urlData.url_info ? `
                                    <p><strong>Visit Count:</strong> ${urlData.url_info.visit_count || 0}</p>
                                    <p><strong>Last Visited:</strong> ${urlData.url_info.last_visited || 'N/A'}</p>
                                    <p><strong>Response Time:</strong> ${urlData.url_info.avg_response_time ? urlData.url_info.avg_response_time.toFixed(2) + 's' : 'N/A'}</p>
                                ` : '<p>No URL history available</p>'}
                            </div>
                            
                            ${urlData.content_data ? `
                                <div class="url-details">
                                    <h4>Content Information</h4>
                                    <p><strong>Title:</strong> ${urlData.content_data.title || 'No title'}</p>
                                    <p><strong>Crawled At:</strong> ${urlData.content_data.crawled_at}</p>
                                    <p><strong>Crawl Depth:</strong> ${urlData.content_data.crawl_depth}</p>
                                    <p><strong>Content Length:</strong> ${urlData.content_data.content ? urlData.content_data.content.length : 0} characters</p>
                                    <p><strong>HTML Length:</strong> ${urlData.content_data.html_content ? urlData.content_data.html_content.length : 0} characters</p>
                                    
                                    <h4>Content Preview</h4>
                                    <div style="background: white; padding: 15px; border-radius: 8px; border: 1px solid #e9ecef; max-height: 200px; overflow-y: auto;">
                                        ${urlData.content_data.content ? urlData.content_data.content.substring(0, 500) + (urlData.content_data.content.length > 500 ? '...' : '') : 'No content available'}
                                    </div>
                                    
                                    ${urlData.content_data.links && urlData.content_data.links.length > 0 ? `
                                        <h4>Discovered Links (${urlData.content_data.links.length})</h4>
                                        <div class="links-list">
                                            ${urlData.content_data.links.slice(0, 20).map(link => `<a href="${link}" target="_blank">${link}</a>`).join('')}
                                            ${urlData.content_data.links.length > 20 ? `<p><em>... and ${urlData.content_data.links.length - 20} more links</em></p>` : ''}
                                        </div>
                                    ` : '<p>No links discovered</p>'}
                                </div>
                            ` : '<p>No content data available</p>'}
                        `;
                    } else {
                        content.innerHTML = `<div class="error">Error loading URL details: ${data.error}</div>`;
                    }
                })
                .catch(error => {
                    console.error('Error loading URL details:', error);
                    content.innerHTML = '<div class="error">Error loading URL details</div>';
                });
        }
        
        function closeModal() {
            document.getElementById('url-modal').style.display = 'none';
        }
        
        // Close modal when clicking outside
        window.onclick = function(event) {
            const modal = document.getElementById('url-modal');
            if (event.target === modal) {
                modal.style.display = 'none';
            }
        }
        
        function startAutoRefresh() {
            if (document.getElementById('auto-refresh').checked) {
                refreshInterval = setInterval(refreshQueueState, 2000);
            }
        }
        
        function stopAutoRefresh() {
            if (refreshInterval) {
                clearInterval(refreshInterval);
                refreshInterval = null;
            }
        }
        
        function refreshQueueState() {
            fetch('/api/queue-state')
                .then(response => response.json())
                .then(data => {
                    if (data.success) {
                        updateQueueDisplay(data.data);
                    }
                })
                .catch(error => console.error('Error refreshing queue state:', error));
        }
        
        function updateQueueDisplay(data) {
            // The API returns queue state directly under 'data', not 'data.queue_state'
            const queueState = data;
            const crawlingInProgress = data.processing_urls > 0;
            
            // Update the queue status display
            const display = document.getElementById('queue-status-display');
            if (queueState && (queueState.total_urls > 0 || queueState.completed_urls > 0)) {
                const progressPercent = queueState.total_urls > 0 ? 
                    Math.round((queueState.completed_urls / queueState.total_urls) * 100 * 10) / 10 : 0;
                
                display.innerHTML = `
                    <div class="queue-status ${crawlingInProgress ? 'active' : queueState.completed_urls > 0 ? 'completed' : ''}">
                        <h3>Current Status</h3>
                        
                        <div class="queue-metrics">
                            <div class="metric">
                                <div class="metric-value">${queueState.total_urls || 0}</div>
                                <div class="metric-label">Total URLs</div>
                            </div>
                            <div class="metric">
                                <div class="metric-value">${queueState.queued_urls || 0}</div>
                                <div class="metric-label">Queued</div>
                            </div>
                            <div class="metric">
                                <div class="metric-value">${queueState.processing_urls || 0}</div>
                                <div class="metric-label">Processing</div>
                            </div>
                            <div class="metric">
                                <div class="metric-value">${queueState.completed_urls || 0}</div>
                                <div class="metric-label">Completed</div>
                            </div>
                            <div class="metric">
                                <div class="metric-value">${queueState.failed_urls || 0}</div>
                                <div class="metric-label">Failed</div>
                            </div>
                        </div>
                        
                        ${queueState.current_url ? `
                            <div class="current-url">
                                <strong>Currently Processing:</strong><br>
                                URL: ${queueState.current_url}<br>
                                Depth: ${queueState.current_depth}
                            </div>
                        ` : ''}
                        
                        ${queueState.start_time ? `<p><strong>Started:</strong> ${queueState.start_time}</p>` : ''}
                        
                        ${queueState.estimated_completion ? `<p><strong>Estimated Completion:</strong> ${new Date(queueState.estimated_completion * 1000).toLocaleString()}</p>` : ''}
                        
                        ${queueState.completed_urls > 0 && queueState.total_urls > 0 ? `
                            <div class="progress">
                                <div class="progress-bar">
                                    <div class="progress-fill" style="width: ${progressPercent}%"></div>
                                </div>
                                <p style="text-align: center; margin-top: 5px;">
                                    ${queueState.completed_urls} / ${queueState.total_urls} (${progressPercent}%)
                                </p>
                            </div>
                        ` : ''}
                        
                        ${queueState.errors && queueState.errors.length > 0 ? `
                            <h4>Recent Errors:</h4>
                            <ul>
                            ${queueState.errors.slice(-5).map(error => `<li>${error}</li>`).join('')}
                            </ul>
                        ` : ''}
                    </div>
                `;
            } else {
                display.innerHTML = `
                    <div class="queue-status">
                        <p>No crawl in progress. Start a new crawl to see queue status.</p>
                    </div>
                `;
            }
        }
        
        function stopCrawl() {
            if (confirm('Are you sure you want to stop the current crawl?')) {
                fetch('/api/stop-crawl')
                    .then(response => response.json())
                    .then(data => {
                        if (data.success) {
                            alert('Crawl stop requested. It will stop after completing current URL.');
                            const startBtn = document.getElementById('start-crawl-btn');
                            const stopBtn = document.getElementById('stop-crawl-btn');
                            startBtn.style.display = 'inline-block';
                            stopBtn.style.display = 'none';
                            startBtn.disabled = false;
                            startBtn.innerHTML = '🚀 Start Unlimited Crawling';
                        } else {
                            alert(data.message);
                        }
                    })
                    .catch(error => console.error('Error stopping crawl:', error));
            }
        }
        
        // Auto-refresh checkbox handlers
        document.addEventListener('DOMContentLoaded', function() {
            console.log('DOM loaded, initializing tabs...');
            initializeTabs();
            
            document.getElementById('auto-refresh').addEventListener('change', function() {
                if (this.checked && document.getElementById('queue-tab').style.display !== 'none') {
                    startAutoRefresh();
                } else {
                    stopAutoRefresh();
                }
            });
        });
        
        // Show specific tabs if requested via URL parameters
        {% if show_data %}
            document.addEventListener('DOMContentLoaded', function() {
                setTimeout(() => showTab('data', null), 100);
            });
        {% endif %}
        
        {% if show_history %}
            document.addEventListener('DOMContentLoaded', function() {
                setTimeout(() => showTab('history', null), 100);
            });
        {% endif %}
        
        {% if show_queue %}
            document.addEventListener('DOMContentLoaded', function() {
                setTimeout(() => showTab('queue', null), 100);
            });
        {% endif %}
    </script>
</body>
</html>
""" 