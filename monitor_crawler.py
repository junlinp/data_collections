#!/usr/bin/env python3
"""
Comprehensive Crawler Service Monitor
Continuously monitors crawler service health and logs potential restart causes
"""

import time
import json
import sys
import logging
import requests
import psutil
import subprocess
import signal
from datetime import datetime, timedelta
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('/mnt/rbd0/tmp/monitor.log', mode='a')
    ]
)
logger = logging.getLogger(__name__)

class CrawlerMonitor:
    def __init__(self):
        self.monitoring = True
        self.check_interval = 30  # seconds
        self.alerts = []
        self.last_health_check = {}
        self.restart_count = 0
        
        # Thresholds
        self.memory_warning_threshold = 3000  # MB
        self.memory_critical_threshold = 3500  # MB
        self.response_time_warning = 10  # seconds
        self.response_time_critical = 30  # seconds
        
        # Services to monitor
        self.services = {
            'crawler': {
                'url': 'http://localhost:5001/api/health',
                'container': 'web-crawler-server',
                'critical': True
            },
            'ui': {
                'url': 'http://localhost:5002/api/health',
                'container': 'web-crawler-ui',
                'critical': False
            },
            'mongodb': {
                'container': 'web-crawler-mongodb',
                'critical': True
            },
            'redis': {
                'container': 'data_collections-redis-1',
                'critical': True
            }
        }
        
        logger.info("🔍 Crawler Monitor initialized")
        self.setup_signal_handlers()
    
    def setup_signal_handlers(self):
        """Setup signal handlers for graceful shutdown"""
        signal.signal(signal.SIGTERM, self.signal_handler)
        signal.signal(signal.SIGINT, self.signal_handler)
    
    def signal_handler(self, signum, frame):
        """Handle shutdown signals"""
        logger.info(f"Received signal {signum}, shutting down monitor...")
        self.monitoring = False
        self.save_final_report()
        sys.exit(0)
    
    def get_container_info(self, container_name):
        """Get container information"""
        try:
            # Get container status
            result = subprocess.run(
                ['docker', 'inspect', container_name],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode == 0:
                container_info = json.loads(result.stdout)[0]
                state = container_info['State']
                
                return {
                    'running': state.get('Running', False),
                    'status': state.get('Status', 'unknown'),
                    'started_at': state.get('StartedAt'),
                    'finished_at': state.get('FinishedAt'),
                    'exit_code': state.get('ExitCode'),
                    'error': state.get('Error'),
                    'restart_count': container_info.get('RestartCount', 0),
                    'pid': state.get('Pid')
                }
            else:
                return {'running': False, 'error': 'Container not found'}
                
        except Exception as e:
            logger.error(f"Error getting container info for {container_name}: {e}")
            return {'running': False, 'error': str(e)}
    
    def get_container_stats(self, container_name):
        """Get container resource usage statistics"""
        try:
            result = subprocess.run(
                ['docker', 'stats', '--no-stream', '--format', 
                 'json', container_name],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode == 0 and result.stdout.strip():
                stats = json.loads(result.stdout.strip())
                
                # Parse memory usage
                memory_usage = stats.get('MemUsage', '0B / 0B')
                memory_parts = memory_usage.split(' / ')
                if len(memory_parts) == 2:
                    used_mem = self.parse_memory_size(memory_parts[0])
                    total_mem = self.parse_memory_size(memory_parts[1])
                else:
                    used_mem = total_mem = 0
                
                # Parse CPU percentage
                cpu_percent = stats.get('CPUPerc', '0.00%').replace('%', '')
                
                return {
                    'memory_used_mb': used_mem,
                    'memory_total_mb': total_mem,
                    'cpu_percent': float(cpu_percent) if cpu_percent != 'N/A' else 0,
                    'net_io': stats.get('NetIO', '0B / 0B'),
                    'block_io': stats.get('BlockIO', '0B / 0B'),
                    'pids': stats.get('PIDs', '0')
                }
            else:
                return {}
                
        except Exception as e:
            logger.error(f"Error getting container stats for {container_name}: {e}")
            return {}
    
    def parse_memory_size(self, size_str):
        """Parse memory size string to MB"""
        try:
            size_str = size_str.strip()
            if size_str.endswith('GiB') or size_str.endswith('GB'):
                return float(size_str[:-3]) * 1024
            elif size_str.endswith('MiB') or size_str.endswith('MB'):
                return float(size_str[:-3])
            elif size_str.endswith('KiB') or size_str.endswith('KB'):
                return float(size_str[:-3]) / 1024
            elif size_str.endswith('B'):
                return float(size_str[:-1]) / 1024 / 1024
            else:
                return float(size_str)
        except:
            return 0
    
    def check_service_health(self, service_name, service_config):
        """Check health of a specific service"""
        health_status = {
            'service': service_name,
            'timestamp': datetime.now().isoformat(),
            'healthy': False,
            'response_time': None,
            'status_code': None,
            'error': None,
            'container_info': {},
            'container_stats': {}
        }
        
        # Get container info
        if 'container' in service_config:
            health_status['container_info'] = self.get_container_info(service_config['container'])
            health_status['container_stats'] = self.get_container_stats(service_config['container'])
        
        # Check HTTP health endpoint if available
        if 'url' in service_config:
            try:
                start_time = time.time()
                response = requests.get(
                    service_config['url'], 
                    timeout=15,
                    headers={'User-Agent': 'CrawlerMonitor/1.0'}
                )
                response_time = time.time() - start_time
                
                health_status['response_time'] = response_time
                health_status['status_code'] = response.status_code
                health_status['healthy'] = response.status_code == 200
                
                if response.status_code == 200:
                    try:
                        data = response.json()
                        health_status['response_data'] = data
                    except:
                        pass
                
                # Check response time thresholds
                if response_time > self.response_time_critical:
                    self.add_alert('critical', f"{service_name} response time critical: {response_time:.2f}s")
                elif response_time > self.response_time_warning:
                    self.add_alert('warning', f"{service_name} response time slow: {response_time:.2f}s")
                
            except requests.exceptions.Timeout:
                health_status['error'] = 'Request timeout'
                self.add_alert('critical', f"{service_name} health check timeout")
            except requests.exceptions.ConnectionError:
                health_status['error'] = 'Connection error'
                self.add_alert('critical', f"{service_name} connection error")
            except Exception as e:
                health_status['error'] = str(e)
                self.add_alert('error', f"{service_name} health check error: {e}")
        
        # Check container status
        container_info = health_status.get('container_info', {})
        if not container_info.get('running', False):
            self.add_alert('critical', f"{service_name} container not running")
            
            # Check for restarts
            restart_count = container_info.get('restart_count', 0)
            if restart_count > self.restart_count:
                self.add_alert('critical', f"{service_name} container restarted (count: {restart_count})")
                self.restart_count = restart_count
        
        # Check memory usage
        container_stats = health_status.get('container_stats', {})
        memory_used = container_stats.get('memory_used_mb', 0)
        if memory_used > self.memory_critical_threshold:
            self.add_alert('critical', f"{service_name} memory usage critical: {memory_used:.1f}MB")
        elif memory_used > self.memory_warning_threshold:
            self.add_alert('warning', f"{service_name} memory usage high: {memory_used:.1f}MB")
        
        return health_status
    
    def add_alert(self, level, message):
        """Add an alert to the alerts list"""
        alert = {
            'timestamp': datetime.now().isoformat(),
            'level': level,
            'message': message
        }
        self.alerts.append(alert)
        
        # Log the alert
        if level == 'critical':
            logger.error(f"🚨 CRITICAL: {message}")
        elif level == 'warning':
            logger.warning(f"⚠️ WARNING: {message}")
        else:
            logger.info(f"ℹ️ INFO: {message}")
        
        # Keep only last 100 alerts
        if len(self.alerts) > 100:
            self.alerts = self.alerts[-100:]
    
    def get_system_resources(self):
        """Get system resource information"""
        try:
            return {
                'timestamp': datetime.now().isoformat(),
                'cpu_percent': psutil.cpu_percent(interval=1),
                'memory': {
                    'total': psutil.virtual_memory().total // 1024 // 1024,  # MB
                    'available': psutil.virtual_memory().available // 1024 // 1024,  # MB
                    'used': psutil.virtual_memory().used // 1024 // 1024,  # MB
                    'percent': psutil.virtual_memory().percent
                },
                'disk': {
                    'total': psutil.disk_usage('/').total // 1024 // 1024,  # MB
                    'used': psutil.disk_usage('/').used // 1024 // 1024,  # MB
                    'free': psutil.disk_usage('/').free // 1024 // 1024,  # MB
                    'percent': psutil.disk_usage('/').percent
                },
                'load_average': psutil.getloadavg(),
                'boot_time': psutil.boot_time()
            }
        except Exception as e:
            logger.error(f"Error getting system resources: {e}")
            return {}
    
    def save_monitoring_data(self, data):
        """Save monitoring data to file"""
        try:
            log_dir = Path('/mnt/rbd0/tmp')
            log_dir.mkdir(exist_ok=True)
            
            # Save detailed data
            timestamp = datetime.now().strftime('%Y%m%d_%H')
            log_file = log_dir / f'monitor_data_{timestamp}.jsonl'
            
            with open(log_file, 'a') as f:
                f.write(json.dumps(data) + '\n')
            
            # Save summary
            summary_file = log_dir / 'monitor_summary.json'
            summary = {
                'last_update': datetime.now().isoformat(),
                'alerts_count': len(self.alerts),
                'recent_alerts': self.alerts[-10:] if self.alerts else [],
                'service_status': {
                    name: status.get('healthy', False) 
                    for name, status in data.get('services', {}).items()
                },
                'system_resources': data.get('system_resources', {}),
                'restart_count': self.restart_count
            }
            
            with open(summary_file, 'w') as f:
                json.dump(summary, f, indent=2)
                
        except Exception as e:
            logger.error(f"Error saving monitoring data: {e}")
    
    def run_monitoring_cycle(self):
        """Run a single monitoring cycle"""
        logger.info("🔍 Running monitoring cycle...")
        
        monitoring_data = {
            'timestamp': datetime.now().isoformat(),
            'services': {},
            'system_resources': self.get_system_resources(),
            'alerts': self.alerts[-10:] if self.alerts else []
        }
        
        # Check all services
        for service_name, service_config in self.services.items():
            health_status = self.check_service_health(service_name, service_config)
            monitoring_data['services'][service_name] = health_status
            
            logger.info(f"  {service_name}: {'✅' if health_status['healthy'] else '❌'} "
                       f"{'Container: ' + ('UP' if health_status.get('container_info', {}).get('running') else 'DOWN')}")
        
        # Save monitoring data
        self.save_monitoring_data(monitoring_data)
        
        logger.info(f"✅ Monitoring cycle completed. Alerts: {len(self.alerts)}")
    
    def save_final_report(self):
        """Save final monitoring report"""
        try:
            report = {
                'monitoring_ended': datetime.now().isoformat(),
                'total_alerts': len(self.alerts),
                'alerts_by_level': {},
                'restart_count': self.restart_count,
                'all_alerts': self.alerts
            }
            
            # Count alerts by level
            for alert in self.alerts:
                level = alert['level']
                report['alerts_by_level'][level] = report['alerts_by_level'].get(level, 0) + 1
            
            report_file = Path('/mnt/rbd0/tmp/final_monitor_report.json')
            with open(report_file, 'w') as f:
                json.dump(report, f, indent=2)
            
            logger.info(f"📋 Final monitoring report saved to {report_file}")
            
        except Exception as e:
            logger.error(f"Error saving final report: {e}")
    
    def run(self):
        """Main monitoring loop"""
        logger.info("🚀 Starting crawler monitoring...")
        logger.info(f"Check interval: {self.check_interval} seconds")
        logger.info(f"Monitoring services: {list(self.services.keys())}")
        
        try:
            while self.monitoring:
                self.run_monitoring_cycle()
                time.sleep(self.check_interval)
                
        except KeyboardInterrupt:
            logger.info("Monitoring interrupted by user")
        except Exception as e:
            logger.error(f"Error in monitoring loop: {e}")
        finally:
            logger.info("🛑 Monitoring stopped")
            self.save_final_report()

def main():
    """Main function"""
    print("🔍 Crawler Service Monitor")
    print("=" * 50)
    
    monitor = CrawlerMonitor()
    
    try:
        monitor.run()
    except Exception as e:
        logger.error(f"Monitor failed: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main() 