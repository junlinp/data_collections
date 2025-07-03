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
        
        /* Enhanced Worker Timing Display Styles */
        .timing-section {
            margin-top: 20px;
            padding: 20px;
            background: linear-gradient(135deg, #f8f9fa, #e9ecef);
            border-radius: 15px;
            box-shadow: 0 4px 15px rgba(0,0,0,0.1);
            border: 1px solid #dee2e6;
        }
        
        .timing-header {
            margin-bottom: 15px;
            font-size: 1.1em;
            font-weight: 600;
            color: #495057;
            display: flex;
            align-items: center;
            justify-content: space-between;
        }
        
        .timing-header small {
            color: #6c757d;
            font-weight: 400;
            font-size: 0.85em;
        }
        
        .timing-cards {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(120px, 1fr));
            gap: 12px;
            margin-bottom: 20px;
        }
        
        .timing-card {
            padding: 15px;
            background: white;
            border-radius: 10px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.08);
            border-left: 4px solid #667eea;
            transition: transform 0.2s, box-shadow 0.2s;
            position: relative;
            overflow: hidden;
        }
        
        .timing-card:hover {
            transform: translateY(-2px);
            box-shadow: 0 4px 15px rgba(0,0,0,0.15);
        }
        
        .timing-card.fetch {
            border-left-color: #667eea;
        }
        
        .timing-card.parse {
            border-left-color: #52c41a;
        }
        
        .timing-card.extract {
            border-left-color: #fa8c16;
        }
        
        .timing-card.save {
            border-left-color: #eb2f96;
        }
        
        .timing-card.add_links {
            border-left-color: #722ed1;
        }
        
        .step-name {
            font-size: 14px;
            font-weight: 600;
            color: #343a40;
            margin-bottom: 8px;
        }
        
        .avg-time {
            font-size: 18px;
            font-weight: 700;
            color: #667eea;
            margin-bottom: 4px;
        }
        
        .time-range {
            font-size: 11px;
            color: #6c757d;
            margin-bottom: 4px;
        }
        
        .process-count {
            font-size: 11px;
            color: #6c757d;
            margin-bottom: 8px;
        }
        
        .performance-indicator {
            height: 4px;
            border-radius: 2px;
            margin-top: 8px;
        }
        
        .performance-indicator.excellent {
            background: linear-gradient(90deg, #52c41a, #73d13d);
        }
        
        .performance-indicator.good {
            background: linear-gradient(90deg, #fa8c16, #ffa940);
        }
        
        .performance-indicator.needs-attention {
            background: linear-gradient(90deg, #ff4d4f, #ff7875);
        }
        
        .chart-container {
            margin: 20px 0;
            background: white;
            border-radius: 10px;
            padding: 15px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.08);
        }
        
        .detailed-stats {
            margin-top: 20px;
            background: white;
            border-radius: 10px;
            overflow: hidden;
            box-shadow: 0 2px 8px rgba(0,0,0,0.08);
        }
        
        .timing-table {
            width: 100%;
            border-collapse: collapse;
            font-size: 13px;
        }
        
        .timing-table th {
            background: linear-gradient(135deg, #667eea, #764ba2);
            color: white;
            padding: 12px 10px;
            text-align: left;
            font-weight: 600;
            font-size: 12px;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }
        
        .timing-table td {
            padding: 10px;
            border-bottom: 1px solid #f1f3f4;
        }
        
        .timing-table tr:hover {
            background: #f8f9fa;
        }
        
        .time-value {
            font-family: 'Courier New', monospace;
            font-weight: 600;
            color: #495057;
        }
        
        .count-value {
            font-weight: 600;
            color: #6c757d;
        }
        
        .efficiency {
            padding: 4px 8px;
            border-radius: 12px;
            font-size: 11px;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }
        
        .efficiency.excellent {
            background: linear-gradient(135deg, #52c41a, #73d13d);
            color: white;
        }
        
        .efficiency.good {
            background: linear-gradient(135deg, #fa8c16, #ffa940);
            color: white;
        }
        
        .efficiency.warning {
            background: linear-gradient(135deg, #ff4d4f, #ff7875);
            color: white;
        }
        
        .worker-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 20px;
            padding-bottom: 15px;
            border-bottom: 2px solid #e9ecef;
        }
        
        .worker-status {
            padding: 6px 12px;
            border-radius: 20px;
            font-size: 12px;
            font-weight: 600;
        }
        
        .worker-status.online {
            background: linear-gradient(135deg, #52c41a, #73d13d);
            color: white;
        }
        
        .worker-status.offline {
            background: linear-gradient(135deg, #ff4d4f, #ff7875);
            color: white;
        }
        
        .worker-stats {
            margin-bottom: 20px;
        }
        
        .stat-group {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
            gap: 15px;
            margin-bottom: 15px;
        }
        
        .stat-item {
            padding: 15px;
            background: linear-gradient(135deg, #f8f9fa, #e9ecef);
            border-radius: 10px;
            text-align: center;
            border-left: 4px solid #667eea;
        }
        
        .stat-label {
            display: block;
            font-size: 11px;
            color: #6c757d;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            margin-bottom: 5px;
        }
        
        .stat-value {
            display: block;
            font-size: 20px;
            font-weight: 700;
            color: #495057;
        }
        
        .stat-value.failed {
            color: #ff4d4f;
        }
        
        .worker-details {
            background: #f8f9fa;
            padding: 15px;
            border-radius: 10px;
            font-size: 13px;
        }
        
        .worker-details p {
            margin: 5px 0;
            color: #495057;
        }
        
        .no-timing-data {
            text-align: center;
            padding: 40px;
            background: linear-gradient(135deg, #f8f9fa, #e9ecef);
            border-radius: 15px;
            color: #6c757d;
            font-size: 16px;
        }
        
        .step-icon {
            display: inline-block;
            width: 12px;
            height: 12px;
            border-radius: 50%;
            margin-right: 8px;
        }
        
        .step-icon.fetch {
            background: #667eea;
        }
        
        .step-icon.parse {
            background: #52c41a;
        }
        
        .step-icon.extract {
            background: #fa8c16;
        }
        
        .step-icon.save {
            background: #eb2f96;
        }
        
        .step-icon.add_links {
            background: #722ed1;
        }
        
        /* Recent URLs Section Styles */
        .recent-urls-section {
            margin-top: 25px;
            padding: 20px;
            background: white;
            border-radius: 15px;
            box-shadow: 0 4px 15px rgba(0,0,0,0.1);
            border: 1px solid #dee2e6;
        }
        
        .section-header {
            margin-bottom: 15px;
            font-size: 1.1em;
            font-weight: 600;
            color: #495057;
            display: flex;
            align-items: center;
            justify-content: space-between;
        }
        
        .section-header small {
            color: #6c757d;
            font-weight: 400;
            font-size: 0.85em;
        }
        
        .recent-urls-list {
            max-height: 400px;
            overflow-y: auto;
            border-radius: 10px;
        }
        
        .recent-url-item {
            padding: 15px;
            margin-bottom: 10px;
            border-radius: 10px;
            border-left: 4px solid;
            background: #f8f9fa;
            transition: all 0.2s;
        }
        
        .recent-url-item:hover {
            transform: translateX(5px);
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }
        
        .recent-url-item.success {
            border-left-color: #52c41a;
            background: linear-gradient(135deg, #f6ffed, #f0f9ff);
        }
        
        .recent-url-item.error {
            border-left-color: #ff4d4f;
            background: linear-gradient(135deg, #fff1f0, #fff7f7);
        }
        
        .url-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 10px;
        }
        
        .url-domain {
            font-weight: 600;
            color: #495057;
            font-size: 14px;
        }
        
        .url-status {
            padding: 4px 8px;
            border-radius: 12px;
            font-size: 11px;
            font-weight: 600;
            text-transform: uppercase;
        }
        
        .status-success {
            background: linear-gradient(135deg, #52c41a, #73d13d);
            color: white;
        }
        
        .status-error {
            background: linear-gradient(135deg, #ff4d4f, #ff7875);
            color: white;
        }
        
        .url-total-time {
            font-family: 'Courier New', monospace;
            font-weight: 700;
            color: #667eea;
            font-size: 13px;
        }
        
        .url-timings {
            display: flex;
            flex-wrap: wrap;
            gap: 8px;
            margin-bottom: 8px;
        }
        
        .step-timing {
            padding: 3px 8px;
            border-radius: 8px;
            font-size: 10px;
            font-weight: 600;
            color: white;
        }
        
        .step-timing.fetch {
            background: #667eea;
        }
        
        .step-timing.parse {
            background: #52c41a;
        }
        
        .step-timing.extract {
            background: #fa8c16;
        }
        
        .step-timing.save {
            background: #eb2f96;
        }
        
        .step-timing.add_links {
            background: #722ed1;
        }
        
        .url-time {
            font-size: 11px;
            color: #6c757d;
            font-style: italic;
        }
        
        .url-error {
            margin-top: 8px;
            padding: 8px;
            background: #fff2f0;
            border: 1px solid #ffccc7;
            border-radius: 6px;
            color: #cf1322;
            font-size: 11px;
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
                <button onclick="refreshWorkerStatus()" class="btn-secondary">🔄 Refresh Status</button>
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
            // Fetch both worker stats and detailed timing data
            Promise.all([
                fetch('/api/worker-stats', { 
                    method: 'GET',
                    signal: AbortSignal.timeout(5000)
                }),
                fetch('/api/worker-timing-details', { 
                    method: 'GET',
                    signal: AbortSignal.timeout(5000)
                })
            ])
            .then(responses => Promise.all(responses.map(r => r.json())))
            .then(([statsData, timingData]) => {
                if (statsData.success) {
                    updateWorkerStats(statsData.data, timingData.success ? timingData.data : {});
                } else {
                    console.error('Worker stats API error:', statsData.error);
                    refreshWorkerStatusFallback();
                }
            })
            .catch(error => {
                console.error('Error refreshing worker status:', error);
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

        function updateWorkerStats(stats, timingDetails = {}) {
            document.getElementById('total-workers').textContent = stats.total_workers || 0;
            document.getElementById('running-workers').textContent = Object.values(stats.workers || {}).filter(w => w.running).length;
            document.getElementById('system-status').textContent = stats.running ? 'Running' : 'Stopped';
            
            const container = document.getElementById('worker-details-display');
            const workerCards = Object.entries(stats.workers || {}).map(([id, worker]) => {
                const startedAt = worker.started_at ? new Date(parseFloat(worker.started_at) * 1000).toLocaleString() : 'N/A';
                
                // Enhanced step timings display with charts and detailed breakdown
                let stepTimingsHtml = '';
                if (worker.step_timings_summary && Object.keys(worker.step_timings_summary).length > 0) {
                    // Create chart data for this worker
                    const chartId = `timing-chart-${id}`;
                    const chartData = Object.entries(worker.step_timings_summary);
                    
                    stepTimingsHtml = `
                        <div class="timing-section">
                            <div class="timing-header">
                                <strong>📊 Step Timing Performance</strong>
                                <small>(Last 100 URLs processed)</small>
                            </div>
                            
                            <!-- Performance Summary Cards -->
                            <div class="timing-cards">
                                ${chartData.map(([step, stats]) => `
                                    <div class="timing-card ${step}">
                                        <div class="step-name">${step.charAt(0).toUpperCase() + step.slice(1)}</div>
                                        <div class="avg-time">${stats.avg.toFixed(3)}s</div>
                                        <div class="time-range">${stats.min.toFixed(3)}s - ${stats.max.toFixed(3)}s</div>
                                        <div class="process-count">${stats.count} processed</div>
                                        <div class="performance-indicator ${getPerformanceClass(step, stats.avg)}"></div>
                                    </div>
                                `).join('')}
                            </div>
                            
                            <!-- Timing Chart -->
                            <div class="chart-container">
                                <canvas id="${chartId}" width="400" height="200"></canvas>
                            </div>
                            
                            <!-- Detailed Statistics Table -->
                            <div class="detailed-stats">
                                <table class="timing-table">
                                    <thead>
                                        <tr>
                                            <th>Processing Step</th>
                                            <th>Average</th>
                                            <th>Min</th>
                                            <th>Max</th>
                                            <th>Count</th>
                                            <th>Efficiency</th>
                                        </tr>
                                    </thead>
                                    <tbody>
                                        ${chartData.map(([step, stats]) => {
                                            const efficiency = calculateEfficiency(step, stats.avg);
                                            return `
                                                <tr>
                                                    <td><span class="step-icon ${step}"></span>${step.charAt(0).toUpperCase() + step.slice(1)}</td>
                                                    <td class="time-value">${stats.avg.toFixed(3)}s</td>
                                                    <td class="time-value">${stats.min.toFixed(3)}s</td>
                                                    <td class="time-value">${stats.max.toFixed(3)}s</td>
                                                    <td class="count-value">${stats.count}</td>
                                                    <td><span class="efficiency ${efficiency.class}">${efficiency.label}</span></td>
                                                </tr>
                                            `;
                                        }).join('')}
                                    </tbody>
                                </table>
                            </div>
                        </div>
                    `;
                    
                    // Store chart data for later rendering
                    setTimeout(() => renderTimingChart(chartId, chartData), 100);
                } else {
                    stepTimingsHtml = '<div class="no-timing-data">⏱️ No timing data available yet</div>';
                }
                
                // Add recent URL processing details
                let recentUrlsHtml = '';
                const workerTimingData = timingDetails[id];
                if (workerTimingData && workerTimingData.recent_timings && workerTimingData.recent_timings.length > 0) {
                    recentUrlsHtml = `
                        <div class="recent-urls-section">
                            <div class="section-header">
                                <strong>🕒 Recent URL Processing</strong>
                                <small>(Last ${workerTimingData.recent_timings.length} URLs)</small>
                            </div>
                            <div class="recent-urls-list">
                                ${workerTimingData.recent_timings.map(urlData => {
                                    const totalTime = urlData.total_time.toFixed(3);
                                    const timeAgo = formatTimeAgo(urlData.timestamp);
                                    const statusClass = urlData.status_code === 200 ? 'success' : 'error';
                                    const domain = new URL(urlData.url).hostname;
                                    
                                    return `
                                        <div class="recent-url-item ${statusClass}">
                                            <div class="url-header">
                                                <span class="url-domain">${domain}</span>
                                                <span class="url-status status-${statusClass}">${urlData.status_code || 'Error'}</span>
                                                <span class="url-total-time">${totalTime}s</span>
                                            </div>
                                            <div class="url-timings">
                                                ${Object.entries(urlData.timings).map(([step, time]) => `
                                                    <span class="step-timing ${step}">
                                                        ${step}: ${time.toFixed(3)}s
                                                    </span>
                                                `).join('')}
                                            </div>
                                            <div class="url-time">${timeAgo}</div>
                                            ${urlData.error ? `<div class="url-error">Error: ${urlData.error}</div>` : ''}
                                        </div>
                                    `;
                                }).join('')}
                            </div>
                        </div>
                    `;
                }
                
                return `
                <div class="worker-card ${worker.running ? 'running' : 'stopped'}">
                    <div class="worker-header">
                        <h4>🔧 Worker ${id}</h4>
                        <div class="worker-status ${worker.running ? 'online' : 'offline'}">
                            ${worker.running ? '🟢 Running' : '🔴 Stopped'}
                        </div>
                    </div>
                    
                    <div class="worker-stats">
                        <div class="stat-group">
                            <div class="stat-item">
                                <span class="stat-label">Processed URLs</span>
                                <span class="stat-value">${worker.processed_urls || 0}</span>
                            </div>
                            <div class="stat-item">
                                <span class="stat-label">Failed URLs</span>
                                <span class="stat-value failed">${worker.failed_urls || 0}</span>
                            </div>
                            <div class="stat-item">
                                <span class="stat-label">Success Rate</span>
                                <span class="stat-value">${calculateSuccessRate(worker.processed_urls, worker.failed_urls)}%</span>
                            </div>
                        </div>
                        
                        <div class="worker-details">
                            <p><strong>Started:</strong> ${startedAt}</p>
                            <p><strong>Thread:</strong> ${worker.thread_alive ? '✅ Active' : '❌ Inactive'}</p>
                            <p><strong>Total Processed:</strong> ${worker.total_urls || 0} URLs</p>
                        </div>
                    </div>
                    
                                         ${stepTimingsHtml}
                     
                     ${recentUrlsHtml}
                 </div>
             `}).join('');
            
            container.innerHTML = workerCards;
        }

        function getPerformanceClass(step, avgTime) {
            // Define performance thresholds for each step
            const thresholds = {
                fetch: { good: 2.0, warning: 5.0 },
                parse: { good: 0.1, warning: 0.5 },
                extract: { good: 0.2, warning: 1.0 },
                save: { good: 0.5, warning: 2.0 },
                add_links: { good: 0.1, warning: 0.5 }
            };
            
            const threshold = thresholds[step] || { good: 1.0, warning: 3.0 };
            
            if (avgTime <= threshold.good) return 'excellent';
            if (avgTime <= threshold.warning) return 'good';
            return 'needs-attention';
        }

        function calculateEfficiency(step, avgTime) {
            const performance = getPerformanceClass(step, avgTime);
            switch (performance) {
                case 'excellent': return { class: 'excellent', label: '🚀 Excellent' };
                case 'good': return { class: 'good', label: '👍 Good' };
                default: return { class: 'warning', label: '⚠️ Slow' };
            }
        }

        function calculateSuccessRate(processed, failed) {
            const total = (processed || 0) + (failed || 0);
            if (total === 0) return 100;
            return ((processed || 0) / total * 100).toFixed(1);
        }

        function formatTimeAgo(timestamp) {
            const now = Date.now() / 1000;
            const diff = now - timestamp;
            
            if (diff < 60) return `${Math.floor(diff)}s ago`;
            if (diff < 3600) return `${Math.floor(diff / 60)}m ago`;
            if (diff < 86400) return `${Math.floor(diff / 3600)}h ago`;
            return `${Math.floor(diff / 86400)}d ago`;
        }

        function renderTimingChart(chartId, chartData) {
            const canvas = document.getElementById(chartId);
            if (!canvas) return;
            
            const ctx = canvas.getContext('2d');
            const labels = chartData.map(([step]) => step.charAt(0).toUpperCase() + step.slice(1));
            const avgTimes = chartData.map(([, stats]) => stats.avg);
            const minTimes = chartData.map(([, stats]) => stats.min);
            const maxTimes = chartData.map(([, stats]) => stats.max);
            
            new Chart(ctx, {
                type: 'bar',
                data: {
                    labels: labels,
                    datasets: [
                        {
                            label: 'Average Time (s)',
                            data: avgTimes,
                            backgroundColor: 'rgba(102, 126, 234, 0.8)',
                            borderColor: 'rgba(102, 126, 234, 1)',
                            borderWidth: 1
                        },
                        {
                            label: 'Min Time (s)',
                            data: minTimes,
                            backgroundColor: 'rgba(46, 204, 113, 0.6)',
                            borderColor: 'rgba(46, 204, 113, 1)',
                            borderWidth: 1
                        },
                        {
                            label: 'Max Time (s)',
                            data: maxTimes,
                            backgroundColor: 'rgba(231, 76, 60, 0.6)',
                            borderColor: 'rgba(231, 76, 60, 1)',
                            borderWidth: 1
                        }
                    ]
                },
                options: {
                    responsive: true,
                    plugins: {
                        title: {
                            display: true,
                            text: 'Step Processing Times'
                        },
                        legend: {
                            position: 'top'
                        }
                    },
                    scales: {
                        y: {
                            beginAtZero: true,
                            title: {
                                display: true,
                                text: 'Time (seconds)'
                            }
                        },
                        x: {
                            title: {
                                display: true,
                                text: 'Processing Steps'
                            }
                        }
                    }
                }
            });
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
    
    <!-- Chart.js CDN for timing visualizations -->
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
</body>
</html>
""" 