#!/usr/bin/env python3
"""
Emergency Redis Logging Fix
This script drastically reduces Redis logging to prevent memory overflow
"""

import time
import os

def apply_emergency_fix():
    """Apply emergency fix to redis_queue_manager.py"""
    
    redis_manager_path = "/app/redis_queue_manager.py"
    
    # Read the current file
    with open(redis_manager_path, 'r') as f:
        content = f.read()
    
    # Create a backup
    backup_path = f"{redis_manager_path}.backup_{int(time.time())}"
    with open(backup_path, 'w') as f:
        f.write(content)
    
    print(f"✅ Backup created: {backup_path}")
    
    # Apply aggressive logging reduction
    fixes = [
        # Reduce health check frequency to every 30 minutes
        ('self.last_health_check = time.time() - 60  # Force first check', 
         'self.last_health_check = time.time() - 1800  # Force first check'),
        
        # Reduce operation testing frequency to every 30 minutes  
        ('self.last_operation_test = time.time() - 60  # Force first test',
         'self.last_operation_test = time.time() - 1800  # Force first test'),
        
        # Change health check interval to 30 minutes
        ('if time.time() - self.last_health_check > 600:',
         'if time.time() - self.last_health_check > 1800:'),
        
        # Change operation test interval to 30 minutes
        ('if time.time() - self.last_operation_test > 1200:',
         'if time.time() - self.last_operation_test > 1800:'),
        
        # Remove excessive logging
        ('logger.info("✅ Redis connection healthy - ping: {:.3f}s".format(ping_time))',
         '# logger.info("✅ Redis connection healthy - ping: {:.3f}s".format(ping_time))'),
        
        ('logger.info("✅ Redis read/write operations working")',
         '# logger.info("✅ Redis read/write operations working")'),
        
        ('logger.info("✅ Redis queue manager initialized successfully")',
         '# logger.info("✅ Redis queue manager initialized successfully")'),
        
        ('logger.info("🚀 Initializing Redis queue manager")',
         '# logger.info("🚀 Initializing Redis queue manager")'),
        
        ('logger.info("Redis connection: {}:{}, DB: {}".format(host, port, db))',
         '# logger.info("Redis connection: {}:{}, DB: {}".format(host, port, db))'),
    ]
    
    modified_content = content
    changes_made = 0
    
    for old, new in fixes:
        if old in modified_content:
            modified_content = modified_content.replace(old, new)
            changes_made += 1
            print(f"✅ Applied fix: {old[:50]}...")
    
    # Write the modified content
    with open(redis_manager_path, 'w') as f:
        f.write(modified_content)
    
    print(f"✅ Emergency fix applied - {changes_made} changes made")
    print(f"✅ Redis logging drastically reduced")
    
    return changes_made

if __name__ == "__main__":
    print("🚨 EMERGENCY REDIS LOGGING FIX")
    print("=" * 50)
    
    changes = apply_emergency_fix()
    
    if changes > 0:
        print("\n✅ SUCCESS: Emergency fix applied!")
        print("The container should now use much less memory.")
        print("You may need to restart the container for changes to take effect.")
    else:
        print("\n❌ WARNING: No changes were made!")
        print("The file may have already been modified or the structure changed.") 