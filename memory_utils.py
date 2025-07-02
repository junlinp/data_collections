import psutil
import gc
import logging
import os
from typing import Optional

logger = logging.getLogger(__name__)

def get_memory_usage() -> dict:
    """Get current memory usage statistics."""
    process = psutil.Process(os.getpid())
    memory_info = process.memory_info()
    
    return {
        'rss': memory_info.rss,  # Resident Set Size (physical memory)
        'vms': memory_info.vms,  # Virtual Memory Size
        'percent': process.memory_percent(),
        'available': psutil.virtual_memory().available,
        'total': psutil.virtual_memory().total
    }

def log_memory_usage(service_name: str, operation: str = ""):
    """Log current memory usage for monitoring."""
    memory = get_memory_usage()
    operation_text = f" ({operation})" if operation else ""
    
    logger.info(
        f"[{service_name}] Memory usage{operation_text}: "
        f"RSS: {memory['rss'] / 1024 / 1024:.1f}MB, "
        f"VMS: {memory['vms'] / 1024 / 1024:.1f}MB, "
        f"Percent: {memory['percent']:.1f}%"
    )

def force_garbage_collection():
    """Force garbage collection to free memory."""
    collected = gc.collect()
    logger.info(f"Garbage collection freed {collected} objects")
    return collected

def check_memory_threshold(threshold_percent: float = 80.0) -> bool:
    """Check if memory usage is above threshold."""
    memory = get_memory_usage()
    return memory['percent'] > threshold_percent

def optimize_memory(service_name: str, threshold_percent: float = 80.0):
    """Optimize memory usage if above threshold."""
    if check_memory_threshold(threshold_percent):
        logger.warning(f"[{service_name}] Memory usage above {threshold_percent}%, optimizing...")
        force_garbage_collection()
        log_memory_usage(service_name, "after optimization")
        return True
    return False

def set_memory_limit(limit_mb: int):
    """Set a soft memory limit (requires psutil)."""
    try:
        import resource
        # Convert MB to bytes
        limit_bytes = limit_mb * 1024 * 1024
        resource.setrlimit(resource.RLIMIT_AS, (limit_bytes, limit_bytes))
        logger.info(f"Set memory limit to {limit_mb}MB")
    except ImportError:
        logger.warning("resource module not available, cannot set memory limit")
    except Exception as e:
        logger.error(f"Failed to set memory limit: {e}")

class MemoryMonitor:
    """Context manager for monitoring memory usage during operations."""
    
    def __init__(self, service_name: str, operation: str):
        self.service_name = service_name
        self.operation = operation
        self.start_memory = None
        
    def __enter__(self):
        self.start_memory = get_memory_usage()
        log_memory_usage(self.service_name, f"before {self.operation}")
        return self
        
    def __exit__(self, exc_type, exc_val, exc_tb):
        end_memory = get_memory_usage()
        memory_diff = end_memory['rss'] - self.start_memory['rss']
        
        logger.info(
            f"[{self.service_name}] {self.operation} completed. "
            f"Memory change: {memory_diff / 1024 / 1024:+.1f}MB"
        )
        
        # Force garbage collection after memory-intensive operations
        if memory_diff > 50 * 1024 * 1024:  # If more than 50MB was used
            force_garbage_collection() 