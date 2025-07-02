"""
HTML templates for the web crawler
Separated from the main application for better maintainability
Uses queue-based system with workers
"""

HTML_TEMPLATE = """
<!doctype html>
<html>
<head>
    <title>Queue-Based Web Crawler - Interactive Dashboard</title>
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
        
        .queue-settings { 
            background: white; 
            padding: 25px; 
            border-radius: 15px; 
            margin: 20px 0;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }
        .queue-settings label { 
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
        
        .worker-status { 
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
        
        .queue-info { 
            background: linear-gradient(135deg, #e7f3ff 0%, #b3d9ff 100%);
            border: 2px solid #339af0; 
            padding: 25px; 
            border-radius: 15px; 
            margin: 20px 0;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }
        .queue-info h3 { 
            color: #0056b3; 
            margin-top: 0;
            font-size: 1.5em;
        }
        
        .worker-info { 
            background: linear-gradient(135deg, #fff2cc 0%, #ffeaa7 100%);
            border: 2px solid #fcc419; 
            padding: 15px; 
            border-radius: 10px; 
            margin: 15px 0;
        }
        
        .24h-rule-info { 
            background: linear-gradient(135deg, #e8f5e8 0%, #c3e6cb 100%);
            border: 2px solid #51cf66; 
            padding: 25px; 
            border-radius: 15px; 
            margin: 20px 0;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }
        .24h-rule-info h3 { 
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
            margin: 20px 0;
            display: flex;
            justify-content: center;
            align-items: center;
            gap: 15px;
        }
        .pagination button {
            padding: 8px 16px;
            font-size: 14px;
        }
        
        .loading {
            display: inline-block;
            width: 16px;
            height: 16px;
            border: 2px solid #ffffff;
            border-radius: 50%;
            border-top-color: transparent;
            animation: spin 1s ease-in-out infinite;
        }
        @keyframes spin {
            to { transform: rotate(360deg); }
        }
        
        .worker-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 20px;
            margin: 20px 0;
        }
        .worker-card {
            background: white;
            padding: 20px;
            border-radius: 10px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            border-left: 4px solid #667eea;
        }
        .worker-card.running {
            border-left-color: #51cf66;
        }
        .worker-card.stopped {
            border-left-color: #ff6b6b;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🕷️ Queue-Based Web Crawler</h1>
            <p>Add URLs to queue • Workers process automatically • 24-hour visit tracking</p>
        </div>
        
        {% if message %}
            <div class="results">
                <div class="{{ 'success' if success else 'error' }}">{{ message }}</div>
            </div>
        {% endif %}
        
        <div class="nav-tabs">
            <a href="#queue" class="active" onclick="showTab('queue', event)">Add to Queue</a>
            <a href="#status" onclick="showTab('status', event)">Queue Status</a>
            <a href="#workers" onclick="showTab('workers', event)">Workers</a>
            <a href="#data" onclick="showTab('data', event)">View Data</a>
        </div>
        
        <div id="queue-tab" style="display: block;">
            <div class="queue-settings">
                <h3>📝 Add URL to Queue</h3>
                <div class="form-group">
                    <label for="url">Website URL:</label>
                    <input name="url" id="url" type="text" placeholder="https://example.com" value="{{ url or '' }}" required>
                </div>
                <div class="form-group">
                    <label for="priority">Priority:</label>
                    <select id="priority" style="padding: 12px 15px; font-size: 16px; border: 2px solid #e1e5e9; border-radius: 8px;">
                        <option value="0">Normal</option>
                        <option value="1">High</option>
                        <option value="-1">Low</option>
                    </select>
                </div>
                <div class="24h-rule-info">
                    <h3>🕐 24-Hour Rule</h3>
                    <p><strong>Smart Queueing:</strong> URLs are only added to queue if not visited in the last 24 hours</p>
                    <p><strong>Automatic Processing:</strong> Workers continuously process queued URLs</p>
                    <p><strong>No Duplicates:</strong> Same URL won't be queued multiple times</p>
                </div>
                <div class="form-group">
                    <button type="button" id="add-url-btn" onclick="addUrlToQueue()">
                        ➕ Add to Queue
                    </button>
                </div>
            </div>

            <div id="queue-message"></div>
        </div>
        
        <div id="status-tab" style="display: none;">
            <h2>📊 Queue Status</h2>
            
            <div class="auto-refresh">
                <input type="checkbox" id="auto-refresh" checked>
                <label for="auto-refresh">Auto-refresh every 2 seconds</label>
                <button onclick="refreshQueueStatus()" style="margin-left: 10px;">Refresh Now</button>
                <span id="status-tab-indicator" style="margin-left: 10px; color: #28a745; font-weight: bold; display: none;">✓ Status Tab Active</span>
            </div>
            
            <div id="queue-stats-display" class="stats-grid">
                <div class="stat-card">
                    <h4>📈 Queue Statistics</h4>
                    <p><strong>Completed URLs:</strong> <span id="completed-urls">-</span></p>
                    <p><strong>Failed URLs:</strong> <span id="failed-urls">-</span></p>
                </div>
                <div class="stat-card">
                    <h4>📊 Content Database</h4>
                    <p><strong>Total Records:</strong> <span id="content-records">-</span></p>
                    <p><strong>Total Visits:</strong> <span id="total-visits">-</span></p>
                </div>
                <div class="stat-card">
                    <h4>🗃️ Redis Queue Status</h4>
                    <p><strong>Pending in Redis:</strong> <span id="redis-queue-length">{{ redis_queue_length }}</span></p>
                    <p><strong>Visited (24h):</strong> <span id="redis-visited-count">{{ redis_visited_count }}</span></p>
                </div>
            </div>
            <div style="margin: 30px 0;">
                <h4>📈 Queue Size Trend (Last 24h)</h4>
                <canvas id="queueTrendChart" height="80"></canvas>
            </div>
            <div id="pending-urls-display">
                <h3>⏳ Pending URLs</h3>
                <div id="pending-urls-table"></div>
            </div>
            
            <div class="queue-actions">
                <button onclick="clearQueue()" class="btn-danger">🗑️ Clear Queue</button>
                <button onclick="startWorkers()" class="btn-success">▶️ Start Workers</button>
                <button onclick="stopWorkers()" class="btn-warning">⏹️ Stop Workers</button>
            </div>
        </div>
        
        <div id="workers-tab" style="display: none;">
            <h2>🔧 Worker Management</h2>
            
            <div class="worker-info">
                <strong>Worker System:</strong><br>
                • <strong>Background Processing:</strong> Workers run continuously in background<br>
                • <strong>Automatic Queue Processing:</strong> Workers pick up URLs automatically<br>
                • <strong>Scalable:</strong> Add/remove workers as needed<br>
                • <strong>Fault Tolerant:</strong> Failed URLs are marked and tracked
            </div>
            
            <div id="worker-stats-display" class="stats-grid">
                <div class="stat-card">
                    <h4>👥 Worker Status</h4>
                    <p><strong>Total Workers:</strong> <span id="total-workers">-</span></p>
                    <p><strong>Running Workers:</strong> <span id="running-workers">-</span></p>
                    <p><strong>System Status:</strong> <span id="system-status">-</span></p>
                </div>
            </div>
            
            <div id="worker-details-display" class="worker-grid">
                <!-- Worker details will be populated here -->
            </div>
            
            <div class="queue-actions">
                <button onclick="addWorker()" class="btn-success">➕ Add Worker</button>
                <button onclick="startWorkers()" class="btn-success">▶️ Start All Workers</button>
                <button onclick="stopWorkers()" class="btn-warning">⏹️ Stop All Workers</button>
            </div>
        </div>
        
        <div id="data-tab" style="display: none;">
            <h2>📊 Crawled Data</h2>
            
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
                                <th>Status</th>
                                <th>Response Time</th>
                                <th>Crawled At</th>
                                <th>Actions</th>
                            </tr>
                        </thead>
                        <tbody id="data-tbody">
                        {% for item in crawled_data %}
                            <tr>
                                <td><a href="{{ item.url }}" target="_blank">{{ item.url }}</a></td>
                                <td>{{ item.title or 'No title' }}</td>
                                <td class="content-preview">{{ item.content[:100] }}{% if item.content|length > 100 %}...{% endif %}</td>
                                <td>
                                    <span class="status-{{ 'completed' if item.status_code == 200 else 'failed' }}">
                                        {{ item.status_code or 'Unknown' }}
                                    </span>
                                </td>
                                <td>{{ "%.2f"|format(item.response_time or 0) }}s</td>
                                <td>{{ item.crawled_at }}</td>
                                <td>
                                    <a href="/html/{{ item.url | urlencode }}" class="html-link" target="_blank">
                                        View HTML
                                    </a>
                                </td>
                            </tr>
                        {% endfor %}
                        </tbody>
                    </table>
                {% else %}
                    <p>No data has been crawled yet. Add URLs to the queue to start crawling.</p>
                {% endif %}
            </div>
        </div>
    </div>

    <script>
        let autoRefreshInterval;
        let currentPage = 1;
        let totalPages = 1;
        let currentSearch = '';

        function showTab(tabName, event) {
            event.preventDefault();
            
            // Hide all tabs
            document.querySelectorAll('[id$="-tab"]').forEach(tab => {
                tab.style.display = 'none';
            });
            
            // Remove active class from all tab links
            document.querySelectorAll('.nav-tabs a').forEach(link => {
                link.classList.remove('active');
            });
            
            // Show selected tab
            document.getElementById(tabName + '-tab').style.display = 'block';
            
            // Add active class to clicked link
            event.target.classList.add('active');
            
            // Handle tab-specific actions
            if (tabName === 'status') {
                startAutoRefresh();
                setTimeout(() => {
                    refreshQueueStatus();
                }, 100);
            } else if (tabName === 'workers') {
                startAutoRefresh();
                setTimeout(() => {
                    refreshWorkerStatus();
                }, 100);
            } else if (tabName === 'data') {
                stopAutoRefresh();
                setTimeout(() => {
                    loadData();
                }, 100);
            } else {
                stopAutoRefresh();
            }
        }

        function addUrlToQueue() {
            const url = document.getElementById('url').value.trim();
            const priority = document.getElementById('priority').value;
            
            if (!url) {
                showMessage('Please enter a URL', 'error');
                return;
            }
            
            const addBtn = document.getElementById('add-url-btn');
            addBtn.disabled = true;
            addBtn.innerHTML = '<span class="loading"></span> Adding...';
            
            fetch('/api/add-url', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ url: url, priority: parseInt(priority) })
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    showMessage(data.message, 'success');
                    document.getElementById('url').value = '';
                } else {
                    showMessage(data.error || 'Error adding URL to queue', 'error');
                }
            })
            .catch(error => {
                console.error('Error adding URL to queue:', error);
                showMessage('Error adding URL to queue', 'error');
            })
            .finally(() => {
                addBtn.disabled = false;
                addBtn.innerHTML = '➕ Add to Queue';
            });
        }

        function showMessage(message, type) {
            const messageDiv = document.getElementById('queue-message');
            messageDiv.innerHTML = `<div class="${type}">${message}</div>`;
            setTimeout(() => {
                messageDiv.innerHTML = '';
            }, 5000);
        }

        function refreshQueueStatus() {
            fetch('/api/queue-stats')
                .then(response => response.json())
                .then(data => {
                    if (data.success) {
                        updateQueueStats(data.data);
                    }
                })
                .catch(error => console.error('Error refreshing queue status:', error));
            
            fetch('/api/database-stats')
                .then(response => response.json())
                .then(data => {
                    if (data.success) {
                        updateDatabaseStats(data.data);
                    }
                })
                .catch(error => console.error('Error refreshing database stats:', error));
            
            fetch('/api/pending-urls')
                .then(response => response.json())
                .then(data => {
                    if (data.success) {
                        updatePendingUrls(data.data);
                    }
                })
                .catch(error => console.error('Error fetching pending URLs:', error));
        }

        function updateQueueStats(stats) {
            document.getElementById('completed-urls').textContent = stats.completed_urls || 0;
            document.getElementById('failed-urls').textContent = stats.failed_urls || 0;
        }

        function updateDatabaseStats(stats) {
            document.getElementById('content-records').textContent = stats.content_records || 0;
            document.getElementById('total-visits').textContent = stats.total_visits || 0;
        }

        function updatePendingUrls(urls) {
            const container = document.getElementById('pending-urls-table');
            if (urls.length === 0) {
                container.innerHTML = '<p>No pending URLs in queue.</p>';
                return;
            }
            
            const table = `
                <table class="data-table">
                    <thead>
                        <tr>
                            <th>URL</th>
                            <th>Domain</th>
                            <th>Priority</th>
                        </tr>
                    </thead>
                    <tbody>
                        ${urls.map(urlString => {
                            try {
                                const url = new URL(urlString);
                                const domain = url.hostname;
                                return `
                                    <tr>
                                        <td><a href="${urlString}" target="_blank">${urlString}</a></td>
                                        <td>${domain}</td>
                                        <td>
                                            <span class="priority-medium">Normal</span>
                                        </td>
                                    </tr>
                                `;
                            } catch (e) {
                                return `
                                    <tr>
                                        <td><a href="${urlString}" target="_blank">${urlString}</a></td>
                                        <td>Invalid URL</td>
                                        <td>
                                            <span class="priority-medium">Normal</span>
                                        </td>
                                    </tr>
                                `;
                            }
                        }).join('')}
                    </tbody>
                </table>
            `;
            container.innerHTML = table;
        }

        function refreshWorkerStatus() {
            fetch('/api/worker-stats', { 
                method: 'GET',
                signal: AbortSignal.timeout(5000) // 5 second timeout
            })
                .then(response => response.json())
                .then(data => {
                    if (data.success) {
                        updateWorkerStats(data.data);
                    } else {
                        console.error('Worker stats API error:', data.error);
                        // Try fallback to health endpoint
                        refreshWorkerStatusFallback();
                    }
                })
                .catch(error => {
                    console.error('Error refreshing worker status:', error);
                    // Try fallback to health endpoint
                    refreshWorkerStatusFallback();
                });
        }

        function refreshWorkerStatusFallback() {
            // Fallback to health endpoint for basic worker status
            fetch('/api/health', { 
                method: 'GET',
                signal: AbortSignal.timeout(3000) // 3 second timeout
            })
                .then(response => response.json())
                .then(data => {
                    if (data.workers_running !== undefined) {
                        document.getElementById('total-workers').textContent = '2'; // Default worker count
                        document.getElementById('running-workers').textContent = data.workers_running ? '2' : '0';
                        document.getElementById('system-status').textContent = data.workers_running ? 'Running' : 'Stopped';
                        
                        // Show basic worker info
                        const container = document.getElementById('worker-details-display');
                        container.innerHTML = `
                            <div class="worker-card ${data.workers_running ? 'running' : 'stopped'}">
                                <h4>Worker Status (Basic)</h4>
                                <p><strong>Status:</strong> ${data.workers_running ? '🟢 Running' : '🔴 Stopped'}</p>
                                <p><strong>Note:</strong> Detailed stats unavailable due to database lock</p>
                                <p><strong>Queue:</strong> ${data.queue_stats ? data.queue_stats.completed_urls : 'Unknown'} completed URLs</p>
                            </div>
                        `;
                    }
                })
                .catch(error => {
                    console.error('Error with fallback worker status:', error);
                    // Show error in UI
                    document.getElementById('total-workers').textContent = 'Error';
                    document.getElementById('running-workers').textContent = 'Error';
                    document.getElementById('system-status').textContent = 'Error';
                });
        }

        function updateWorkerStats(stats) {
            document.getElementById('total-workers').textContent = stats.total_workers || 0;
            document.getElementById('running-workers').textContent = Object.values(stats.workers || {}).filter(w => w.running).length;
            document.getElementById('system-status').textContent = stats.running ? 'Running' : 'Stopped';
            
            const container = document.getElementById('worker-details-display');
            const workerCards = Object.entries(stats.workers || {}).map(([id, worker]) => {
                const startedAt = worker.started_at ? new Date(parseFloat(worker.started_at) * 1000).toLocaleString() : 'N/A';
                return `
                <div class="worker-card ${worker.running ? 'running' : 'stopped'}">
                    <h4>Worker ${id}</h4>
                    <p><strong>Status:</strong> ${worker.running ? '🟢 Running' : '🔴 Stopped'}</p>
                    <p><strong>Processed URLs:</strong> ${worker.processed_urls || 0}</p>
                    <p><strong>Failed URLs:</strong> ${worker.failed_urls || 0}</p>
                    <p><strong>Total URLs:</strong> ${worker.total_urls || 0}</p>
                    <p><strong>Started At:</strong> ${startedAt}</p>
                    <p><strong>Thread Alive:</strong> ${worker.thread_alive ? 'Yes' : 'No'}</p>
                </div>
            `}).join('');
            
            container.innerHTML = workerCards;
        }

        function startAutoRefresh() {
            if (autoRefreshInterval) {
                clearInterval(autoRefreshInterval);
            }
            autoRefreshInterval = setInterval(() => {
                if (document.getElementById('auto-refresh').checked) {
                    // Check which tab is active and refresh accordingly
                    if (document.getElementById('status-tab').style.display !== 'none') {
                        refreshQueueStatus();
                    } else if (document.getElementById('workers-tab').style.display !== 'none') {
                        refreshWorkerStatus();
                    }
                }
            }, 2000);
        }

        function stopAutoRefresh() {
            if (autoRefreshInterval) {
                clearInterval(autoRefreshInterval);
                autoRefreshInterval = null;
            }
        }

        function clearQueue() {
            if (confirm('Are you sure you want to clear the queue? This will remove all pending URLs.')) {
                fetch('/api/clear-queue', { method: 'POST' })
                    .then(response => response.json())
                    .then(data => {
                        if (data.success) {
                            showMessage('Queue cleared successfully', 'success');
                            refreshQueueStatus();
                        } else {
                            showMessage(data.error || 'Error clearing queue', 'error');
                        }
                    })
                    .catch(error => {
                        console.error('Error clearing queue:', error);
                        showMessage('Error clearing queue', 'error');
                    });
            }
        }

        function startWorkers() {
            fetch('/api/start-workers', { method: 'POST' })
                .then(response => response.json())
                .then(data => {
                    if (data.success) {
                        showMessage('Workers started successfully', 'success');
                        refreshWorkerStatus();
                    } else {
                        showMessage(data.error || 'Error starting workers', 'error');
                    }
                })
                .catch(error => {
                    console.error('Error starting workers:', error);
                    showMessage('Error starting workers', 'error');
                });
        }

        function stopWorkers() {
            fetch('/api/stop-workers', { method: 'POST' })
                .then(response => response.json())
                .then(data => {
                    if (data.success) {
                        showMessage('Workers stopped successfully', 'success');
                        refreshWorkerStatus();
                    } else {
                        showMessage(data.error || 'Error stopping workers', 'error');
                    }
                })
                .catch(error => {
                    console.error('Error stopping workers:', error);
                    showMessage('Error stopping workers', 'error');
                });
        }

        function addWorker() {
            fetch('/api/add-worker', { method: 'POST' })
                .then(response => response.json())
                .then(data => {
                    if (data.success) {
                        showMessage('Worker added successfully', 'success');
                        refreshWorkerStatus();
                    } else {
                        showMessage(data.error || 'Error adding worker', 'error');
                    }
                })
                .catch(error => {
                    console.error('Error adding worker:', error);
                    showMessage('Error adding worker', 'error');
                });
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
                limit: 50,
                offset: (currentPage - 1) * 50
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
            
            if (data.length === 0) {
                tbody.innerHTML = '<tr><td colspan="8">No data available</td></tr>';
                return;
            }
            
            tbody.innerHTML = data.map(item => `
                <tr>
                    <td><a href="${item.url}" target="_blank">${item.url}</a></td>
                    <td>${item.title || 'No title'}</td>
                    <td class="content-preview">${item.content ? (item.content.substring(0, 100) + (item.content.length > 100 ? '...' : '')) : ''}</td>
                    <td>
                        <span class="status-${item.status_code === 200 ? 'completed' : 'failed'}">
                            ${item.status_code || 'Unknown'}
                        </span>
                    </td>
                    <td>${item.response_time ? item.response_time.toFixed(2) : '0.00'}s</td>
                    <td>${item.crawled_at}</td>
                    <td>
                        <a href="/html/${encodeURIComponent(item.url)}" class="html-link" target="_blank">
                            View HTML
                        </a>
                    </td>
                </tr>
            `).join('');
        }

        function updateRedisQueueStats() {
            fetch('/queue/redis-status')
                .then(response => response.json())
                .then(data => {
                    document.getElementById('redis-queue-length').textContent = data.queue_length;
                    document.getElementById('redis-visited-count').textContent = data.visited_count;
                });
        }

        // Auto-refresh every 2 seconds if on status tab
        setInterval(function() {
            if (document.getElementById('status-tab').style.display !== 'none') {
                updateRedisQueueStats();
            }
        }, 2000);

        // Chart.js for queue trend
        let queueTrendChart;
        function loadQueueTrendChart() {
            fetch('/queue/history')
                .then(res => res.json())
                .then(data => {
                    const labels = data.map(d => new Date(d.timestamp * 1000).toLocaleTimeString());
                    const values = data.map(d => d.queue_length);
                    const ctx = document.getElementById('queueTrendChart').getContext('2d');
                    if (queueTrendChart) queueTrendChart.destroy();
                    queueTrendChart = new Chart(ctx, {
                        type: 'line',
                        data: {
                            labels: labels,
                            datasets: [{ label: 'Queue Size', data: values, borderColor: '#667eea', fill: false }]
                        },
                        options: {
                            responsive: true,
                            plugins: { legend: { display: false } },
                            scales: { x: { display: true }, y: { beginAtZero: true } }
                        }
                    });
                });
        }
        // Load chart on page load and every 2 minutes
        loadQueueTrendChart();
        setInterval(loadQueueTrendChart, 120000);

        // Initialize on page load
        document.addEventListener('DOMContentLoaded', function() {
            // Set up auto-refresh checkbox
            document.getElementById('auto-refresh').addEventListener('change', function() {
                if (this.checked && document.querySelector('.nav-tabs a.active').getAttribute('href') === '#status') {
                    startAutoRefresh();
                } else {
                    stopAutoRefresh();
                }
            });
            
            // Initial load
            refreshQueueStatus();
            refreshWorkerStatus();
        });
    </script>
</body>
</html>
""" 