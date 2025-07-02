#!/usr/bin/env python3
"""
Memory monitoring script for data collection services.
Run this script to monitor memory usage across all services.
"""

import requests
import time
import json
from datetime import datetime
import argparse

def get_service_status(service_name, port, endpoint="/api/health"):
    """Get service status and memory info if available."""
    try:
        url = f"http://localhost:{port}{endpoint}"
        response = requests.get(url, timeout=5)
        if response.status_code == 200:
            return {
                "status": "healthy",
                "response": response.json() if response.headers.get('content-type', '').startswith('application/json') else response.text
            }
        else:
            return {"status": f"unhealthy (HTTP {response.status_code})"}
    except requests.exceptions.RequestException as e:
        return {"status": f"unreachable: {str(e)}"}

def monitor_services():
    """Monitor all services and their memory usage."""
    services = {
        "crawler": {"port": 5001, "endpoint": "/api/health"},
        "ui": {"port": 5002, "endpoint": "/"},
        "llm-processor": {"port": 5003, "endpoint": "/api/health"},
        "summary-display": {"port": 5004, "endpoint": "/api/health"}
    }
    
    print(f"\n{'='*60}")
    print(f"Memory Monitoring Report - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*60}")
    
    for service_name, config in services.items():
        print(f"\n{service_name.upper()} (Port {config['port']}):")
        print("-" * 40)
        
        status = get_service_status(service_name, config['port'], config['endpoint'])
        print(f"Status: {status['status']}")
        
        if 'response' in status and isinstance(status['response'], dict):
            # Check if the service provides memory information
            if 'memory_usage' in status['response']:
                memory = status['response']['memory_usage']
                print(f"Memory Usage: {memory}")
            elif 'stats' in status['response'] and 'memory' in status['response']['stats']:
                memory = status['response']['stats']['memory']
                print(f"Memory Usage: {memory}")
        
        print()

def continuous_monitoring(interval=30):
    """Continuously monitor services at specified interval."""
    print(f"Starting continuous memory monitoring (interval: {interval}s)")
    print("Press Ctrl+C to stop")
    
    try:
        while True:
            monitor_services()
            time.sleep(interval)
    except KeyboardInterrupt:
        print("\nMonitoring stopped.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Monitor memory usage of data collection services")
    parser.add_argument("--continuous", "-c", action="store_true", 
                       help="Run continuous monitoring")
    parser.add_argument("--interval", "-i", type=int, default=30,
                       help="Monitoring interval in seconds (default: 30)")
    
    args = parser.parse_args()
    
    if args.continuous:
        continuous_monitoring(args.interval)
    else:
        monitor_services() 