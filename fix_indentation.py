#!/usr/bin/env python3
"""
Fix Indentation Error in Redis Queue Manager
This script fixes the indentation error caused by commenting out logging statements
"""

import time

def fix_indentation():
    """Fix indentation error in redis_queue_manager.py"""
    
    redis_manager_path = "/app/redis_queue_manager.py"
    
    print("🔧 Reading Redis queue manager file...")
    
    # Read the current file
    with open(redis_manager_path, 'r') as f:
        content = f.read()
    
    # Create a backup
    backup_path = f"{redis_manager_path}.indentation_backup_{int(time.time())}"
    with open(backup_path, 'w') as f:
        f.write(content)
    
    print(f"✅ Backup created: {backup_path}")
    
    # Split into lines for easier processing
    lines = content.split('\n')
    
    # Find and fix empty if/else blocks
    for i, line in enumerate(lines):
        # Look for commented out logging statements that left empty blocks
        if line.strip().startswith('# logger.info') or line.strip().startswith('# logger.warning'):
            # Check if this was the only statement in an if block
            if i > 0 and lines[i-1].strip().endswith(':'):
                # Add a pass statement to make the block valid
                lines[i] = line + '\n                pass  # Added to fix empty block'
    
    # Write the fixed content
    fixed_content = '\n'.join(lines)
    with open(redis_manager_path, 'w') as f:
        f.write(fixed_content)
    
    print("✅ Indentation error fixed")
    
    return True

if __name__ == "__main__":
    print("🔧 FIXING INDENTATION ERROR")
    print("=" * 40)
    
    if fix_indentation():
        print("✅ SUCCESS: Indentation error fixed!")
    else:
        print("❌ FAILED: Could not fix indentation error") 