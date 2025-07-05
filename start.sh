#!/bin/bash

# Web Crawler Services Startup Script with Enhanced Monitoring

echo "🚀 Starting Web Crawler Services with Enhanced Monitoring..."
echo "Timestamp: $(date)"
echo "Host: $(hostname)"
echo "User: $(whoami)"
echo "Working Directory: $(pwd)"

# Create log directory
mkdir -p /mnt/rbd0/tmp
LOG_FILE="/mnt/rbd0/tmp/startup_$(date +%Y%m%d_%H%M%S).log"
exec > >(tee -a "$LOG_FILE") 2>&1

echo "📝 Logging startup process to: $LOG_FILE"

# Function to log system resources
log_system_resources() {
    echo "📊 System Resources:"
    echo "  Memory: $(free -h | grep '^Mem:' | awk '{print $3 "/" $2}')"
    echo "  Disk: $(df -h / | tail -1 | awk '{print $3 "/" $2 " (" $5 " used)"}')"
    echo "  CPU Load: $(uptime | awk -F'load average:' '{print $2}')"
    echo "  Processes: $(ps aux | wc -l)"
}

# Function to check Docker health
check_docker_health() {
    echo "🐳 Checking Docker status..."
    if ! docker info > /dev/null 2>&1; then
        echo "❌ Docker is not running. Please start Docker first."
        exit 1
    fi
    
    echo "✅ Docker is running"
    echo "  Version: $(docker --version)"
    echo "  Containers: $(docker ps -q | wc -l) running"
    echo "  Images: $(docker images -q | wc -l) total"
}

# Function to check Docker Compose
check_docker_compose() {
    echo "🔧 Checking Docker Compose..."
    if ! command -v docker-compose &> /dev/null; then
        echo "❌ Docker Compose is not installed. Please install Docker Compose first."
        exit 1
    fi
    
    echo "✅ Docker Compose is available"
    echo "  Version: $(docker-compose --version)"
}

# Function to cleanup old containers
cleanup_old_containers() {
    echo "🧹 Cleaning up old containers..."
    
    # Stop existing containers
    docker-compose down --remove-orphans 2>/dev/null || true
    
    # Remove dangling containers
    dangling=$(docker ps -a -q -f status=exited 2>/dev/null | wc -l)
    if [ "$dangling" -gt 0 ]; then
        echo "  Removing $dangling exited containers..."
        docker ps -a -q -f status=exited | xargs docker rm 2>/dev/null || true
    fi
    
    # Remove dangling images
    dangling_images=$(docker images -f "dangling=true" -q 2>/dev/null | wc -l)
    if [ "$dangling_images" -gt 0 ]; then
        echo "  Removing $dangling_images dangling images..."
        docker images -f "dangling=true" -q | xargs docker rmi 2>/dev/null || true
    fi
    
    echo "✅ Cleanup completed"
}

# Function to monitor container startup
monitor_container_startup() {
    local service_name=$1
    local max_wait=$2
    local wait_time=0
    
    echo "⏳ Monitoring $service_name startup (max wait: ${max_wait}s)..."
    
    while [ $wait_time -lt $max_wait ]; do
        if docker-compose ps "$service_name" | grep -q "Up"; then
            echo "✅ $service_name is running"
            return 0
        fi
        
        sleep 5
        wait_time=$((wait_time + 5))
        echo "  Waiting for $service_name... (${wait_time}s/${max_wait}s)"
    done
    
    echo "❌ $service_name failed to start within ${max_wait}s"
    echo "📋 Container logs for $service_name:"
    docker-compose logs --tail=20 "$service_name"
    return 1
}

# Function to check service health
check_service_health() {
    local service_name=$1
    local url=$2
    local max_attempts=$3
    
    echo "🔍 Checking $service_name health at $url..."
    
    for i in $(seq 1 $max_attempts); do
        if curl -f -s "$url" > /dev/null 2>&1; then
            echo "✅ $service_name is healthy"
            return 0
        fi
        
        echo "  Health check attempt $i/$max_attempts failed, retrying..."
        sleep 10
    done
    
    echo "❌ $service_name health check failed after $max_attempts attempts"
    return 1
}

# Function to save startup state
save_startup_state() {
    local state_file="/mnt/rbd0/tmp/startup_state.json"
    
    cat > "$state_file" << EOF
{
    "startup_time": "$(date -Iseconds)",
    "hostname": "$(hostname)",
    "docker_version": "$(docker --version)",
    "compose_version": "$(docker-compose --version)",
    "system_info": {
        "memory": "$(free -h | grep '^Mem:' | awk '{print $3 "/" $2}')",
        "disk": "$(df -h / | tail -1 | awk '{print $3 "/" $2}')",
        "load": "$(uptime | awk -F'load average:' '{print $2}')"
    },
    "log_file": "$LOG_FILE"
}
EOF

    echo "💾 Startup state saved to: $state_file"
}

# Main execution starts here
echo "=================== CRAWLER STARTUP PROCESS ==================="

# Log initial system state
log_system_resources

# Check prerequisites
check_docker_health
check_docker_compose

# Cleanup old containers
cleanup_old_containers

# Log system resources before startup
echo "📊 System resources before startup:"
log_system_resources

# Build and start services
echo "🏗️ Building and starting services..."
if ! docker-compose up --build -d; then
    echo "❌ Failed to start services"
    echo "📋 Docker compose logs:"
    docker-compose logs
    exit 1
fi

echo "✅ Services started, waiting for initialization..."

# Monitor core services startup
monitor_container_startup "mongodb" 120 || exit 1
monitor_container_startup "redis" 60 || exit 1
monitor_container_startup "crawler" 180 || exit 1

# Wait for services to be ready
echo "⏳ Waiting for services to initialize..."
sleep 30

# Log system resources after startup
echo "📊 System resources after startup:"
log_system_resources

# Check service health
echo "🔍 Performing health checks..."

health_failed=0

if ! check_service_health "MongoDB" "http://localhost:27017" 3; then
    health_failed=$((health_failed + 1))
fi

if ! check_service_health "Crawler" "http://localhost:5001/api/health" 5; then
    health_failed=$((health_failed + 1))
fi

if ! check_service_health "Unified Web" "http://localhost:5000/api/health" 3; then
    health_failed=$((health_failed + 1))
fi

# Show running containers
echo "📋 Running containers:"
docker-compose ps

# Show container resource usage
echo "📊 Container resource usage:"
docker stats --no-stream --format "table {{.Container}}\t{{.CPUPerc}}\t{{.MemUsage}}\t{{.NetIO}}\t{{.BlockIO}}"

# Save startup state for monitoring
save_startup_state

# Final status
echo ""
echo "=================== STARTUP SUMMARY ==================="
if [ $health_failed -eq 0 ]; then
    echo "🎉 All services started successfully!"
    echo "🚀 Unified Web Interface: http://localhost:5000"
    echo "🔧 Crawler Server: http://localhost:5001"
    echo "📊 All functionality (UI, LLM, Summaries): http://localhost:5000"
else
    echo "⚠️ Some services failed health checks ($health_failed failed)"
    echo "📋 Check the logs above for more details"
fi

echo ""
echo "📝 Useful commands:"
echo "  View logs: docker-compose logs -f"
echo "  Stop services: docker-compose down"
echo "  Restart service: docker-compose restart <service_name>"
echo "  View startup log: cat $LOG_FILE"
echo ""
echo "🔍 Monitoring enabled - check logs in /mnt/rbd0/tmp/" 