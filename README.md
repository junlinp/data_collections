# Web Crawler with AI Summarization

A comprehensive web crawling and AI summarization system with a unified modern web interface. The system consists of three main components:

1. **Web Crawler Server** - Crawls websites and stores content in MongoDB
2. **Unified Web Interface** - Single interface for all functionality (crawling, AI processing, summaries)
3. **Storage Services** - MongoDB for data persistence and Redis for queue management

## Features

- **Web Crawling**: Crawl websites with rate limiting
- **Content Storage**: Persistent MongoDB database storage
- **AI Summarization**: Generate structured summaries using local LLM models
- **Modern UI**: Clean, responsive web interface
- **Health Monitoring**: Built-in health checks for all services
- **Docker Support**: Complete containerized deployment
- **Proxy Support**: Configurable HTTP/HTTPS proxy settings

## Prerequisites

### Local LLM Setup

This system uses local LLM models instead of cloud APIs. You need to set up Ollama on your host machine:

1. **Install Ollama**:
   ```bash
   # On Linux/macOS
   curl -fsSL https://ollama.ai/install.sh | sh
   
   # Or download from https://ollama.ai/download
   ```

2. **Start Ollama service**:
   ```bash
   ollama serve
   ```

3. **Download a model** (e.g., Llama 2):
   ```bash
   ollama pull llama2
   ```

4. **Verify installation**:
   ```bash
   curl http://localhost:11434/api/tags
   ```

### Docker and Docker Compose

Ensure you have Docker and Docker Compose installed on your system.

## Quick Start

1. **Clone the repository**:
   ```bash
   git clone <repository-url>
   cd data_collections
   ```

2. **Start the services**:
   ```bash
   docker-compose up -d
   ```

3. **Access the services**:
   - **Unified Web Interface: http://localhost:5000** (All functionality in one place)
   - Crawler API: http://localhost:5001

## Service Architecture

### 1. MongoDB Database (Port 27017)

**Purpose**: Primary database for storing web content and summaries.

**Features**:
- Document-based storage for web content and summaries
- Automatic indexing for performance
- Scalable and flexible schema
- Persistent storage in `/mnt/rbd0/crawler_data/mongodb`

**Collections**:
- `web_content` - Stored crawled web pages
- `url_history` - URL processing history
- `summaries` - AI-generated summaries

**Environment Variables**:
- `MONGO_INITDB_ROOT_USERNAME` - Admin username (default: admin)
- `MONGO_INITDB_ROOT_PASSWORD` - Admin password (default: password123)
- `MONGO_INITDB_DATABASE` - Database name (default: crawler_db)

### 2. Web Crawler Server (Port 5001)

**Purpose**: Crawls websites and stores content in MongoDB.

**Features**:
- Configurable rate limiting
- Proxy support for network access
- URL deduplication and history tracking
- Health monitoring
- MongoDB integration for content storage

**API Endpoints**:
- `GET /api/health` - Health check
- `POST /api/crawl` - Start a new crawl
- `GET /api/status` - Get crawl status
- `GET /api/urls` - Get crawled URLs
- `GET /api/content/<url>` - Get content for specific URL

**Environment Variables**:
- `CRAWLER_PORT` - Server port (default: 5001)
- `DEBUG` - Debug mode (default: False)
- `HTTP_PROXY` / `HTTPS_PROXY` - Proxy settings
- `MONGODB_URI` - MongoDB connection string
- `MONGODB_DATABASE` - MongoDB database name

### 2. Web UI (Port 5002)

**Purpose**: Modern web interface for managing crawls and viewing results.

**Features**:
- Real-time crawl status monitoring
- URL management and search
- Content preview
- Responsive design

**Environment Variables**:
- `UI_PORT` - Server port (default: 5002)
- `CRAWLER_SERVER_URL` - Crawler API URL
- `DEBUG` - Debug mode (default: False)

### 3. LLM Processor (Port 5003)

**Purpose**: Processes crawled content using local LLM models to generate summaries.

**Features**:
- Local LLM integration (Ollama)
- Structured summary generation
- Key points extraction
- Sentiment analysis
- Fallback processing when LLM is unavailable
- MongoDB integration for content and summary storage

**API Endpoints**:
- `GET /api/health` - Health check with LLM status
- `POST /api/process-all` - Process all unprocessed URLs
- `POST /api/process-url` - Process specific URL
- `GET /api/status` - Get processing status
- `GET /api/summaries` - Get all summaries (paginated)
- `GET /api/summary/<url>` - Get summary for specific URL

**Environment Variables**:
- `LLM_PORT` - Server port (default: 5003)
- `DEBUG` - Debug mode (default: False)
- `MONGODB_URI` - MongoDB connection string
- `MONGODB_DATABASE` - MongoDB database name
- `LOCAL_LLM_URL` - Local LLM server URL (default: http://host.docker.internal:11434)
- `LOCAL_LLM_MODEL` - LLM model name (default: deepseek-r1:latest)

### 4. Summary Display Server (Port 5004)

**Purpose**: Web interface for viewing and managing AI-generated summaries.

**Features**:
- Summary browsing and search
- Processing status monitoring
- Pagination support
- Direct LLM processor integration
- MongoDB integration for summary retrieval

**API Endpoints**:
- `GET /api/health` - Health check
- `GET /api/summaries` - Get summaries from MongoDB
- `POST /api/process-all` - Trigger processing (proxied to LLM processor)
- `GET /api/status` - Get status (proxied to LLM processor)

**Environment Variables**:
- `SUMMARY_PORT` - Server port (default: 5004)
- `DEBUG` - Debug mode (default: False)
- `MONGODB_URI` - MongoDB connection string
- `MONGODB_DATABASE` - MongoDB database name
- `LLM_PROCESSOR_URL` - LLM processor API URL

## Database Schema

### MongoDB Collections

The system uses MongoDB with the following collections:

#### web_content Collection
```javascript
{
  _id: ObjectId,
  url: String (unique),
  title: String,
  html_content: String,
  text_content: String,
  parent_url: String,
  created_at: Date,
  updated_at: Date
}
```

#### url_history Collection
```javascript
{
  _id: ObjectId,
  url: String,
  status: String,
  created_at: Date
}
```

#### summaries Collection
```javascript
{
  _id: ObjectId,
  url: String (unique),
  title: String,
  summary: String,
  key_points: String,
  sentiment: String,
  word_count: Number,
  processing_time: Number,
  created_at: Date,
  updated_at: Date
}
```

**Indexes**:
- `web_content.url` (unique)
- `web_content.created_at`
- `url_history.url`
- `url_history.created_at`
- `url_history.status`
- `summaries.url` (unique)
- `summaries.created_at`
- `summaries.sentiment`

## Usage

### Starting a Crawl

1. Open the Web UI at http://localhost:5002
2. Enter a URL to crawl
3. Click "Start Crawl"
4. Monitor progress in real-time

### Generating Summaries

1. Ensure Ollama is running with a model loaded
2. Open the Summary Display at http://localhost:5004
3. Click "Process All URLs" to generate summaries for all crawled content
4. View generated summaries with key points and sentiment analysis

### API Usage

**Start a crawl**:
```bash
curl -X POST http://localhost:5001/api/crawl \
  -H "Content-Type: application/json" \
  -d '{"url": "https://example.com"}'
```

**Process all URLs for summarization**:
```bash
curl -X POST http://localhost:5003/api/process-all
```

**Get summaries**:
```bash
curl http://localhost:5003/api/summaries?page=1&per_page=10
```

## Configuration

### Local LLM Configuration

The system is configured to use Ollama by default. You can customize the LLM setup:

1. **Change the model**:
   ```bash
   # Pull a different model
   ollama pull mistral
   
   # Update environment variable
   export LOCAL_LLM_MODEL=mistral
   ```

2. **Customize LLM settings** in `llm_processor.py`:
   - Temperature and other generation parameters
   - Prompt templates
   - Text processing limits

### Proxy Configuration

If you need to use a proxy for internet access:

```yaml
environment:
  - HTTP_PROXY=http://your-proxy:port
  - HTTPS_PROXY=http://your-proxy:port
  - NO_PROXY=localhost,127.0.0.1
```

### Database Persistence

All databases are stored in `/mnt/rbd0/crawler_data` on the host machine and mounted into the containers. Ensure this directory exists and has proper permissions.

## Troubleshooting

### LLM Processor Issues

1. **LLM server not available**:
   - Ensure Ollama is running: `ollama serve`
   - Check if model is downloaded: `ollama list`
   - Verify API endpoint: `curl http://localhost:11434/api/tags`

2. **Processing fails**:
   - Check logs: `docker-compose logs llm-processor`
   - Verify database connectivity
   - Check if content exists in source database

### Crawler Issues

1. **403 Forbidden errors**:
   - Some sites have anti-bot protection
   - Try different user agents or proxy settings
   - Consider adding delays between requests

2. **Network connectivity**:
   - Verify proxy settings
   - Check container network configuration
   - Ensure host machine has internet access

### Database Issues

1. **Data not persisting**:
   - Verify volume mounts in docker-compose.yml
   - Check host directory permissions
   - Ensure MongoDB data directory exists and has proper permissions

2. **MongoDB connection issues**:
   - Check MongoDB service is running: `docker-compose ps mongodb`
   - Verify MongoDB credentials in environment variables
   - Check MongoDB logs: `docker-compose logs mongodb`
   - Ensure MongoDB port 27017 is accessible

3. **Database performance**:
   - Monitor MongoDB memory usage
   - Check index usage and performance
   - Consider MongoDB optimization settings

## Development

### Local Development

1. **Clone and setup**:
   ```bash
   git clone <repository-url>
   cd data_collections
   ```

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   pip install -r requirements_llm.txt
   ```

3. **Run services individually**:
   ```bash
   # Terminal 1: Crawler
   python crawler_server.py
   
   # Terminal 2: UI
   python ui_server.py
   
   # Terminal 3: LLM Processor
   python llm_processor.py
   
   # Terminal 4: Summary Display
   python summary_display_server.py
   ```

### Adding New Features

1. **New API endpoints**: Add routes to the respective Flask applications
2. **Database changes**: Update schemas and migration scripts
3. **UI improvements**: Modify HTML templates and JavaScript
4. **LLM enhancements**: Customize prompts and processing logic

### Testing

1. **Unit tests**: Add tests for individual components
2. **Integration tests**: Test service interactions
3. **End-to-end tests**: Test complete workflows

## Security Considerations

- The system runs in containers with limited privileges
- Database files should have appropriate permissions
- Consider using secrets management for sensitive configuration
- Monitor resource usage and implement rate limiting
- Regular security updates for base images

## Performance Optimization

- Adjust crawl delays based on target site policies
- Optimize database queries for large datasets
- Consider using connection pooling for database connections
- Monitor memory usage of LLM processing
- Implement caching for frequently accessed data

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## Support

For issues and questions:
1. Check the troubleshooting section
2. Review the logs
3. Create an issue with detailed information 