#!/usr/bin/env python3
"""
Targeted Redis Logging Fix
This script fixes the actual f-string logging patterns found in redis_queue_manager.py
"""

import time
import subprocess

def apply_targeted_fix():
    """Apply targeted fix to redis_queue_manager.py"""
    
    redis_manager_path = "/app/redis_queue_manager.py"
    
    print("🔧 Reading current Redis queue manager file...")
    
    # Read the current file
    with open(redis_manager_path, 'r') as f:
        content = f.read()
    
    # Create a backup
    backup_path = f"{redis_manager_path}.targeted_backup_{int(time.time())}"
    with open(backup_path, 'w') as f:
        f.write(content)
    
    print(f"✅ Backup created: {backup_path}")
    
    # Apply targeted logging reduction for the actual patterns
    fixes = [
        # Comment out the actual logging patterns found
        ('        logger.info(f"🚀 Initializing Redis queue manager")',
         '        # logger.info(f"🚀 Initializing Redis queue manager")'),
        
        ('        logger.info(f"Redis connection: {host}:{port}, DB: {db}")',
         '        # logger.info(f"Redis connection: {host}:{port}, DB: {db}")'),
        
        ('        logger.info(f"✅ Redis queue manager initialized successfully")',
         '        # logger.info(f"✅ Redis queue manager initialized successfully")'),
        
        ('                logger.info(f"✅ Redis connection healthy - ping: {ping_time:.3f}s")',
         '                # logger.info(f"✅ Redis connection healthy - ping: {ping_time:.3f}s")'),
        
        ('                        logger.info("✅ Redis reconnection successful")',
         '                        # logger.info("✅ Redis reconnection successful")'),
        
        # Also comment out any remaining patterns
        ('logger.info("✅ Redis connection healthy")',
         '# logger.info("✅ Redis connection healthy")'),
        
        ('logger.warning("⚠️ Redis read/write test failed")',
         '# logger.warning("⚠️ Redis read/write test failed")'),
    ]
    
    modified_content = content
    changes_made = 0
    
    for old, new in fixes:
        if old in modified_content:
            modified_content = modified_content.replace(old, new)
            changes_made += 1
            print(f"✅ Commented out: {old[:60]}...")
    
    # Write the modified content
    with open(redis_manager_path, 'w') as f:
        f.write(modified_content)
    
    print(f"✅ Targeted fix applied - {changes_made} changes made")
    
    return changes_made

def restart_container():
    """Restart the container to apply changes"""
    print("\n🔄 Restarting container to apply changes...")
    try:
        result = subprocess.run(['docker', 'restart', 'web-crawler-server'], 
                              capture_output=True, text=True, timeout=30)
        if result.returncode == 0:
            print("✅ Container restarted successfully")
            return True
        else:
            print(f"❌ Container restart failed: {result.stderr}")
            return False
    except Exception as e:
        print(f"❌ Error restarting container: {e}")
        return False

if __name__ == "__main__":
    print("🎯 TARGETED REDIS LOGGING FIX")
    print("=" * 50)
    
    changes = apply_targeted_fix()
    
    if changes > 0:
        print(f"\n✅ SUCCESS: {changes} logging statements commented out!")
        print("Redis logging has been drastically reduced.")
        print("This should significantly reduce memory usage.")
    else:
        print("\n❌ WARNING: No changes were made!")
        print("The patterns may have already been modified.") 