# Queue-Based Web Crawler System

This is a modern, queue-based web crawler system that implements a worker architecture with 24-hour visit tracking. The system is designed to be scalable, fault-tolerant, and respectful of web servers.

## 🏗️ Architecture Overview

### Core Components

1. **Queue Manager** (`queue_manager.py`)
   - Manages URL queuing with 24-hour visit tracking
   - Prevents duplicate URLs from being queued
   - Tracks URL status (pending, processing, completed, failed)
   - Maintains visit history for compliance

2. **Worker System** (`crawler_worker.py`)
   - Background workers that continuously process URLs from the queue
   - Scalable: can add/remove workers dynamically
   - Fault-tolerant: failed URLs are marked and tracked
   - Each worker runs in its own thread

3. **Crawler Server** (`crawler_server.py`)
   - REST API endpoints for queue and worker management
   - Handles URL addition, queue statistics, worker control
   - Provides content retrieval endpoints

4. **UI Server** (`ui_server.py`)
   - Web interface for managing the crawler system
   - Real-time queue and worker status monitoring
   - Data viewing and management interface

## 🚀 Key Features

### 24-Hour Visit Tracking
- URLs are only added to the queue if not visited in the last 24 hours
- Prevents unnecessary re-crawling of recently visited pages
- Respectful of web servers and reduces load

### Queue-Based Processing
- URLs are added to a queue instead of being crawled immediately
- Workers continuously process URLs from the queue
- Priority system for URL processing (high, normal, low)

### Worker Management
- Multiple workers can run simultaneously
- Workers can be started, stopped, and added dynamically
- Each worker processes URLs independently
- Fault tolerance: failed URLs are tracked separately

### Real-Time Monitoring
- Live queue statistics (pending, processing, completed, failed)
- Worker status monitoring
- Real-time data viewing

## 📋 API Endpoints

### Queue Management
- `POST /api/add-url` - Add URL to queue
- `GET /api/queue-stats` - Get queue statistics
- `GET /api/pending-urls` - Get pending URLs
- `POST /api/clear-queue` - Clear all pending URLs

### Worker Management
- `POST /api/start-workers` - Start workers
- `POST /api/stop-workers` - Stop workers
- `POST /api/add-worker` - Add a new worker
- `GET /api/worker-stats` - Get worker statistics

### Data Retrieval
- `GET /api/crawled-data` - Get crawled content
- `GET /api/html-content` - Get HTML content for specific URL
- `GET /api/database-stats` - Get database statistics

### Legacy Support
- `POST /api/start-crawl` - Legacy endpoint (now adds to queue)
- `POST /api/stop-crawl` - Legacy endpoint (now stops workers)
- `GET /api/crawl-status` - Legacy endpoint (now shows queue/worker status)

## 🛠️ Installation and Setup

### Prerequisites
```bash
pip install -r requirements_crawler.txt
```

### Starting the System

1. **Start the Crawler Server**:
   ```bash
   python crawler_server.py
   ```
   The crawler server will start on port 5001 and automatically start workers.

2. **Start the UI Server**:
   ```bash
   python ui_server.py
   ```
   The UI server will start on port 5000.

3. **Access the Web Interface**:
   Open your browser and go to `http://localhost:5000`

## 📖 Usage Guide

### Adding URLs to Queue

1. **Via Web Interface**:
   - Go to the "Add to Queue" tab
   - Enter the URL you want to crawl
   - Select priority (Normal, High, Low)
   - Click "Add to Queue"

2. **Via API**:
   ```bash
   curl -X POST http://localhost:5001/api/add-url \
     -H "Content-Type: application/json" \
     -d '{"url": "https://example.com", "priority": 0}'
   ```

### Monitoring Queue Status

1. **Via Web Interface**:
   - Go to the "Queue Status" tab
   - View real-time statistics
   - See pending URLs
   - Monitor worker activity

2. **Via API**:
   ```bash
   curl http://localhost:5001/api/queue-stats
   ```

### Managing Workers

1. **Via Web Interface**:
   - Go to the "Workers" tab
   - View worker status
   - Start/stop workers
   - Add new workers

2. **Via API**:
   ```bash
   # Start workers
   curl -X POST http://localhost:5001/api/start-workers \
     -H "Content-Type: application/json" \
     -d '{"num_workers": 2}'
   
   # Stop workers
   curl -X POST http://localhost:5001/api/stop-workers
   ```

### Viewing Crawled Data

1. **Via Web Interface**:
   - Go to the "View Data" tab
   - Browse crawled content
   - Search through data
   - View HTML content

2. **Via API**:
   ```bash
   curl http://localhost:5001/api/crawled-data
   ```

## 🔧 Configuration

### Environment Variables

- `CONTENT_DB_PATH` - Path to content database (default: `/app/data/web_crawler.db`)
- `QUEUE_DB_PATH` - Path to queue database (default: `/app/data/queue_manager.db`)
- `CRAWLER_SERVER_URL` - Crawler server URL for UI (default: `http://localhost:5001`)
- `UI_PORT` - UI server port (default: `5000`)
- `DEBUG` - Enable debug mode (default: `False`)

### Database Files

The system uses two SQLite databases:

1. **Content Database** (`web_crawler.db`)
   - Stores crawled content, titles, HTML
   - Tracks worker information and response times

2. **Queue Database** (`queue_manager.db`)
   - Manages URL queue and status
   - Tracks visit history for 24-hour rule

## 🧪 Testing

Run the test script to verify the system is working:

```bash
python test_queue_system.py
```

This will test:
- Health checks
- URL queueing
- 24-hour rule
- Worker management
- Data retrieval
- UI server functionality

## 🔄 Migration from Old System

The new system maintains backward compatibility with the old crawling system:

- Legacy endpoints still work but now use the queue system
- Old data is preserved and accessible
- UI has been updated but maintains familiar interface

### Key Changes

1. **URL Addition**: Instead of starting immediate crawling, URLs are added to a queue
2. **Worker Processing**: Background workers continuously process queued URLs
3. **24-Hour Rule**: URLs are only queued if not visited in the last 24 hours
4. **Real-Time Monitoring**: Better visibility into queue and worker status

## 🚨 Important Notes

### 24-Hour Rule
- URLs visited within the last 24 hours will not be added to the queue
- This prevents unnecessary re-crawling and respects web servers
- The rule is enforced at the queue level, not during crawling

### Worker Behavior
- Workers run continuously in the background
- They automatically pick up URLs from the queue
- Failed URLs are marked and tracked separately
- Workers can be stopped and started without losing queue data

### Data Persistence
- All queue data is persisted in SQLite databases
- Queue state survives server restarts
- Crawled content is stored permanently

## 🐛 Troubleshooting

### Common Issues

1. **Workers not processing URLs**:
   - Check if workers are running: `GET /api/worker-stats`
   - Start workers: `POST /api/start-workers`
   - Check queue for pending URLs: `GET /api/pending-urls`

2. **URL not being added to queue**:
   - Check if URL was visited in last 24 hours
   - Verify URL format is correct
   - Check server logs for errors

3. **Database errors**:
   - Ensure database directories are writable
   - Check disk space
   - Verify database file permissions

### Logs

The system provides detailed logging:
- Queue manager logs URL operations
- Workers log processing activities
- Servers log API requests and errors

Check the console output for detailed information about system operation.

## 📈 Performance Considerations

- **Worker Count**: Adjust based on your needs and server capacity
- **Queue Size**: Monitor queue size to prevent memory issues
- **Database**: Consider using a more robust database for high-volume crawling
- **Rate Limiting**: Workers include delays to be respectful to servers

## 🔮 Future Enhancements

Potential improvements for the queue system:

1. **Distributed Workers**: Run workers across multiple machines
2. **Advanced Scheduling**: More sophisticated URL prioritization
3. **Rate Limiting**: Per-domain rate limiting
4. **Content Filtering**: Filter content before storing
5. **Export Features**: Export data in various formats
6. **Analytics**: Advanced crawling analytics and reporting 