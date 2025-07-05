# Enhanced Logging System for Crawler Service

This document describes the enhanced logging system added to the crawler service to help detect and diagnose container restart issues.

## 🔍 Overview

The enhanced logging system provides comprehensive monitoring and diagnostics for the crawler service, including:

- **Memory and resource monitoring**
- **Database connection tracking**
- **Detailed error logging with stack traces**
- **Worker thread health monitoring**
- **Startup and shutdown logging**
- **Healthcheck monitoring**
- **Request/response monitoring**

## 📁 Log Files

All log files are stored in `/app/data/` inside containers and `/mnt/rbd0/tmp/` on the host:

### Core Service Logs
- `crawler_server.log` - Main crawler server logs
- `crawler_worker.log` - Worker thread logs
- `mongo_utils.log` - MongoDB connection and operation logs
- `redis_queue.log` - Redis queue operation logs

### Monitoring Logs
- `monitor.log` - Continuous monitoring logs
- `monitor_data_YYYYMMDD_HH.jsonl` - Detailed monitoring data (hourly files)
- `monitor_summary.json` - Current monitoring summary
- `startup_YYYYMMDD_HHMMSS.log` - Startup process logs

## 🚀 Starting with Enhanced Monitoring

### 1. Start Services with Enhanced Startup Script
```bash
# Use the enhanced startup script
./start.sh
```

The enhanced startup script will:
- ✅ Check system resources
- ✅ Verify Docker health
- ✅ Monitor container startup
- ✅ Perform health checks
- ✅ Log all activities

### 2. Start Continuous Monitoring
```bash
# Start the monitoring script in background
python3 monitor_crawler.py &

# Or run in foreground to see real-time monitoring
python3 monitor_crawler.py
```

## 📊 Monitoring Features

### Container Health Monitoring
- **Container status** (running/stopped/restarted)
- **Memory usage** with warning thresholds (3GB warning, 3.5GB critical)
- **CPU usage**
- **Network I/O**
- **Restart count tracking**

### Service Health Monitoring
- **HTTP endpoint health checks**
- **Response time monitoring** (10s warning, 30s critical)
- **Database connectivity tests**
- **Queue operation monitoring**

### System Resource Monitoring
- **System memory usage**
- **Disk usage**
- **CPU load average**
- **Process count**

## 🔍 Detecting Container Restart Issues

### Common Restart Causes and Their Log Signatures

#### 1. Memory Issues (OOM Kills)
**Look for:**
```log
HIGH MEMORY USAGE: 3200.5MB (limit: 4GB)
memory usage critical: 3600.1MB
```

**In system logs:**
```bash
# Check for OOM kills
dmesg | grep -i "killed process"
journalctl -u docker | grep -i "oom"
```

#### 2. Database Connection Issues
**Look for:**
```log
❌ MongoDB connection failed: ServerSelectionTimeoutError
❌ Redis connection error: Connection refused
MongoDB reconnection failed after all attempts
```

#### 3. Unhandled Exceptions
**Look for:**
```log
❌ Unhandled exception in Flask app
❌ Worker thread processing error
Traceback (most recent call last):
```

#### 4. Health Check Failures
**Look for:**
```log
❌ Health check failed after 10.2s
Health check timeout
Container health check failing
```

#### 5. Resource Exhaustion
**Look for:**
```log
Error logging system resources
Too many open files
Connection pool exhausted
```

## 📈 Using Monitoring Data

### Real-time Monitoring
```bash
# Watch live logs
docker-compose logs -f crawler

# Monitor system resources
docker stats

# Check monitoring summary
cat /mnt/rbd0/tmp/monitor_summary.json | jq '.'
```

### Historical Analysis
```bash
# View startup logs
ls /mnt/rbd0/tmp/startup_*.log

# Analyze monitoring data
cat /mnt/rbd0/tmp/monitor_data_*.jsonl | jq '.system_resources.memory'

# Check alerts
cat /mnt/rbd0/tmp/monitor_summary.json | jq '.recent_alerts'
```

### Container Restart Detection
```bash
# Check restart count
docker inspect web-crawler-server | jq '.[0].RestartCount'

# View container events
docker events --filter container=web-crawler-server

# Check exit codes
docker inspect web-crawler-server | jq '.[0].State'
```

## 🛠️ Troubleshooting Commands

### Check Service Health
```bash
# Manual health check
curl -s http://localhost:5001/api/health | jq '.'

# Check all services
docker-compose ps

# View recent logs
docker-compose logs --tail=50 crawler
```

### Analyze Memory Usage
```bash
# Container memory usage
docker stats --no-stream web-crawler-server

# Process memory inside container
docker exec web-crawler-server ps aux --sort=-%mem

# System memory
free -h
```

### Database Connectivity
```bash
# Test MongoDB connection
docker exec web-crawler-mongodb mongosh --eval "db.adminCommand('ping')"

# Test Redis connection
docker exec data_collections-redis-1 redis-cli ping
```

## 📋 Log Analysis Examples

### Find Memory-Related Issues
```bash
# Search for memory warnings
grep -r "memory usage" /mnt/rbd0/tmp/

# Find OOM events
grep -r "killed\|oom\|memory" /var/log/syslog
```

### Track Container Restarts
```bash
# Check restart patterns
grep -r "container restarted" /mnt/rbd0/tmp/

# View restart timeline
docker inspect web-crawler-server | jq '.[0].State | {StartedAt, FinishedAt, RestartCount}'
```

### Database Connection Issues
```bash
# MongoDB connection failures
grep -r "MongoDB.*failed" /mnt/rbd0/tmp/

# Redis connection failures  
grep -r "Redis.*error" /mnt/rbd0/tmp/
```

## ⚠️ Alert Thresholds

The monitoring system uses these default thresholds:

| Metric | Warning | Critical |
|--------|---------|----------|
| Memory Usage | 3000 MB | 3500 MB |
| Response Time | 10 seconds | 30 seconds |
| Container Restarts | 1+ | 5+ |
| Health Check Failures | 3 consecutive | 5 consecutive |

## 🔧 Configuration

### Modify Monitoring Intervals
Edit `monitor_crawler.py`:
```python
self.check_interval = 30  # seconds between checks
```

### Adjust Alert Thresholds
Edit `monitor_crawler.py`:
```python
self.memory_warning_threshold = 3000  # MB
self.memory_critical_threshold = 3500  # MB
```

### Log Levels
Modify logging levels in each service:
```python
logging.basicConfig(level=logging.DEBUG)  # More verbose
logging.basicConfig(level=logging.WARNING)  # Less verbose
```

## 📞 Getting Help

If you're experiencing container restarts:

1. **Check recent alerts**: `cat /mnt/rbd0/tmp/monitor_summary.json`
2. **Review startup logs**: `ls /mnt/rbd0/tmp/startup_*.log`
3. **Analyze resource usage**: `docker stats --no-stream`
4. **Check container status**: `docker inspect web-crawler-server`
5. **Review service logs**: `docker-compose logs --tail=100 crawler`

## 🎯 Quick Diagnosis Checklist

- [ ] Check memory usage (`docker stats`)
- [ ] Verify database connections (`curl http://localhost:5001/api/health`)
- [ ] Check disk space (`df -h`)
- [ ] Review recent alerts (`monitor_summary.json`)
- [ ] Check restart count (`docker inspect`)
- [ ] Review error logs (`grep -r ERROR /mnt/rbd0/tmp/`)
- [ ] Verify network connectivity
- [ ] Check system resources (`top`, `free -h`)

The enhanced logging system provides comprehensive visibility into the crawler service health and should help quickly identify the root cause of any container restart issues. 