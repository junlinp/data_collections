# Advanced Web Crawler - Interactive Dashboard

A powerful, single-threaded web crawler with an interactive web dashboard for unlimited crawling with real-time monitoring and data management.

## 🚀 Features

### Core Crawling
- **Unlimited Crawling**: No depth or page restrictions
- **Single-Threaded**: Simple, reliable, and respectful crawling
- **Smart Discovery**: Automatically finds and queues new URLs
- **Global Queue System**: Persistent URL queue across sessions
- **Priority System**: Different priority levels for URL processing

### Interactive Web Dashboard
- **Modern UI**: Beautiful, responsive design with gradient themes
- **Real-Time Updates**: Live queue status and progress monitoring
- **AJAX Interface**: No page refreshes needed for most operations
- **Search & Pagination**: Advanced data browsing with search functionality
- **Modal Details**: Detailed URL information in popup modals
- **Auto-Refresh**: Configurable automatic updates for queue status

### API Endpoints
- `GET /api/queue-state` - Get current crawl queue status
- `GET /api/global-queue-state` - Get global queue information
- `GET /api/crawled-data` - Get crawled data with pagination and search
- `GET /api/url-details` - Get detailed information about a specific URL
- `POST /api/start-crawl` - Start a new crawl operation
- `GET /api/stop-crawl` - Stop the current crawl
- `POST /api/clear-queue` - Clear the global queue
- `GET /api/stats` - Get URL history statistics
- `GET /api/recent` - Get recently visited URLs
- `GET /api/most-visited` - Get most frequently visited URLs

## 🛠️ Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd data_collections
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Run the web application:
```bash
python web_app.py
```

4. Open your browser and navigate to:
```
http://localhost:5000
```

## 📊 Dashboard Features

### Crawl Website Tab
- **Interactive Form**: AJAX-powered crawl initiation
- **Real-Time Feedback**: Immediate status updates
- **Stop Control**: Ability to stop crawling at any time
- **Progress Tracking**: Live progress indicators

### Queue Status Tab
- **Live Metrics**: Real-time queue statistics
- **Progress Bar**: Visual progress indication
- **Current URL**: Shows currently processing URL
- **Error Logging**: Recent error display
- **Auto-Refresh**: Configurable automatic updates

### Global Queue Tab
- **Queue Management**: View and manage global queue
- **Priority Display**: Visual priority indicators
- **Queue Actions**: Clear all or domain-specific queues
- **Pending URLs**: List of queued URLs

### View Saved Data Tab
- **Search Functionality**: Search URLs and titles
- **Pagination**: Navigate through large datasets
- **Content Preview**: Quick content overview
- **HTML Viewing**: Direct HTML content access
- **URL Details**: Modal popup with detailed information
- **Export Options**: View raw HTML content

### URL History Tab
- **Statistics Overview**: Comprehensive crawling stats
- **Recent Activity**: Recently visited URLs
- **Most Visited**: Frequently accessed pages
- **Time Analysis**: Temporal crawling patterns

## 🔧 Configuration

### Environment Variables
- `FLASK_HOST`: Server host (default: 127.0.0.1)
- `FLASK_PORT`: Server port (default: 5000)
- `FLASK_DEBUG`: Debug mode (default: True)

### Database Files
- `web_crawler.db`: Content database
- `url_history.db`: URL history database
- `global_queue.db`: Global queue database

## 🎯 Usage Examples

### Starting a Crawl
1. Navigate to the "Crawl Website" tab
2. Enter the target URL (e.g., `https://example.com`)
3. Click "Start Unlimited Crawling"
4. Monitor progress in the "Queue Status" tab

### Searching Crawled Data
1. Go to the "View Saved Data" tab
2. Use the search box to find specific URLs or titles
3. Navigate through pages using pagination
4. Click "Details" to view comprehensive URL information

### Monitoring Queue Status
1. Switch to the "Queue Status" tab
2. Enable auto-refresh for real-time updates
3. View current processing URL and progress
4. Monitor error logs and completion statistics

## 🧪 Testing

Run the API test script to verify all endpoints:
```bash
python test_web_api.py
```

## 🔍 API Documentation

### Start Crawl
```bash
curl -X POST http://localhost:5000/api/start-crawl \
  -H "Content-Type: application/json" \
  -d '{"url": "https://example.com"}'
```

### Get Queue State
```bash
curl http://localhost:5000/api/queue-state
```

### Get Crawled Data
```bash
curl "http://localhost:5000/api/crawled-data?page=1&per_page=20&search=example"
```

### Get URL Details
```bash
curl "http://localhost:5000/api/url-details?url=https://example.com"
```

## 🎨 UI Features

### Modern Design
- **Gradient Themes**: Beautiful color schemes
- **Responsive Layout**: Works on desktop and mobile
- **Smooth Animations**: Hover effects and transitions
- **Loading Indicators**: Visual feedback for operations

### Interactive Elements
- **Tab Navigation**: Easy switching between sections
- **Modal Dialogs**: Detailed information popups
- **Real-Time Updates**: Live data without page refresh
- **Search & Filter**: Advanced data exploration

### User Experience
- **Intuitive Interface**: Easy to understand and use
- **Visual Feedback**: Clear status indicators
- **Error Handling**: Graceful error display
- **Mobile Friendly**: Responsive design for all devices

## 🔧 Technical Details

### Architecture
- **Flask Backend**: Python web framework
- **SQLite Databases**: Lightweight data storage
- **AJAX Frontend**: Dynamic user interface
- **Threading**: Background crawl processing

### Data Storage
- **Content Database**: Stores crawled HTML and text
- **URL History**: Tracks visit statistics and metadata
- **Global Queue**: Manages URL processing queue

### Performance
- **Single-Threaded**: Simple and reliable
- **Respectful Crawling**: 0.5 second delays between requests
- **Efficient Storage**: Optimized database queries
- **Real-Time Updates**: Minimal latency for status updates

## 🚀 Future Enhancements

- **Multi-threading Support**: Parallel crawling options
- **Advanced Filtering**: More sophisticated search capabilities
- **Data Export**: CSV/JSON export functionality
- **Scheduling**: Automated crawl scheduling
- **Authentication**: User management system
- **API Rate Limiting**: Enhanced API security

## 📝 License

This project is open source and available under the MIT License. 