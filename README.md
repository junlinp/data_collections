# Web Crawler with Separated UI and Crawler Services

A web crawler application with a clean separation between the UI and crawling logic, containerized with Docker for easy deployment.

## Architecture

The application is split into two separate services:

- **UI Server** (`ui_server.py`): Handles the web interface and user interactions
- **Crawler Server** (`crawler_server.py`): Handles all web crawling operations and data processing

The services communicate via REST API calls, providing better scalability and maintainability.

## Features

- **Separated Services**: Clean separation between UI and crawling logic
- **REST API**: Full REST API for all crawling operations
- **Docker Support**: Containerized deployment with Docker and Docker Compose
- **Health Checks**: Built-in health monitoring for both services
- **Cross-Origin Support**: CORS enabled for service communication
- **Database Persistence**: SQLite databases for URL history and crawled content
- **Real-time Status**: Live queue and crawling status updates

## Quick Start with Docker

### Prerequisites

- Docker
- Docker Compose

### Running the Services

1. **Start both services:**
   ```bash
   ./start.sh
   ```
   Or manually:
   ```bash
   docker-compose up --build -d
   ```

2. **Access the application:**
   - UI Server: http://localhost:5000
   - Crawler Server API: http://localhost:5001

3. **View logs:**
   ```bash
   docker-compose logs -f
   ```

4. **Stop services:**
   ```bash
   docker-compose down
   ```

## Manual Setup (Development)

### Prerequisites

- Python 3.11+
- pip

### Crawler Server Setup

1. **Install dependencies:**
   ```bash
   pip install -r requirements_crawler.txt
   ```

2. **Run the crawler server:**
   ```bash
   python crawler_server.py
   ```
   
   The crawler server will start on port 5001.

### UI Server Setup

1. **Install dependencies:**
   ```bash
   pip install -r requirements_ui.txt
   ```

2. **Set environment variables:**
   ```bash
   export CRAWLER_SERVER_URL=http://localhost:5001
   ```

3. **Run the UI server:**
   ```bash
   python ui_server.py
   ```
   
   The UI server will start on port 5000.

## API Endpoints

### Crawler Server API (Port 5001)

- `GET /api/health` - Health check
- `POST /api/start-crawl` - Start crawling a URL
- `POST /api/stop-crawl` - Stop crawling
- `GET /api/crawl-status` - Get crawling status
- `GET /api/stats` - Get URL statistics
- `GET /api/recent` - Get recently visited URLs
- `GET /api/most-visited` - Get most visited URLs
- `GET /api/url-info` - Get specific URL information
- `GET /api/html-content` - Get HTML content for a URL
- `GET /api/queue-state` - Get queue state
- `GET /api/crawled-data` - Get all crawled data
- `GET /api/url-details` - Get detailed URL information

### UI Server API (Port 5000)

The UI server provides proxy endpoints that forward requests to the crawler server:
- All `/api/*` endpoints are proxied to the crawler server
- `GET /api/health` - UI server health check

## Environment Variables

### Crawler Server
- `CRAWLER_PORT` - Port for the crawler server (default: 5001)
- `DEBUG` - Enable debug mode (default: False)

### UI Server
- `UI_PORT` - Port for the UI server (default: 5000)
- `CRAWLER_SERVER_URL` - URL of the crawler server (default: http://localhost:5001)
- `DEBUG` - Enable debug mode (default: False)

## Docker Configuration

### Services

- **crawler**: Runs the crawler server on port 5001
- **ui**: Runs the UI server on port 5000

### Volumes

- `crawler_data`: Persistent storage for crawler data
- Database files are mounted from the host for persistence

### Networks

- `crawler-network`: Internal network for service communication

## Development

### Project Structure

```
data_collections/
├── crawler_server.py      # Crawler service
├── ui_server.py          # UI service
├── crawler_logic.py      # Core crawling logic
├── url_manager.py        # URL management
├── templates.py          # HTML templates
├── requirements_crawler.txt  # Crawler dependencies
├── requirements_ui.txt      # UI dependencies
├── Dockerfile.crawler    # Crawler Dockerfile
├── Dockerfile.ui         # UI Dockerfile
├── docker-compose.yml    # Docker Compose configuration
└── start.sh             # Startup script
```

### Adding New Features

1. **Crawler Logic**: Add new functionality to `crawler_logic.py`
2. **API Endpoints**: Add new endpoints to `crawler_server.py`
3. **UI Features**: Update `ui_server.py` and `templates.py`
4. **Dependencies**: Update the appropriate requirements file

## Troubleshooting

### Service Communication Issues

1. **Check service health:**
   ```bash
   curl http://localhost:5001/api/health
   curl http://localhost:5000/api/health
   ```

2. **View service logs:**
   ```bash
   docker-compose logs crawler
   docker-compose logs ui
   ```

3. **Restart services:**
   ```bash
   docker-compose restart
   ```

### Database Issues

- Database files are persisted in the host directory
- Check file permissions if databases are not accessible
- Ensure the data directory exists and is writable

## License

This project is open source and available under the MIT License. 