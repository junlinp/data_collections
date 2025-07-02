#!/usr/bin/env python3
"""
Cleanup script to remove SQLite database files that are no longer needed
since the system has migrated to MongoDB
"""

import os
import glob
import shutil

def cleanup_sqlite_files():
    """Remove SQLite database files that are no longer needed"""
    
    # Data directory path
    data_dir = '/mnt/rbd0/crawler_data'
    
    # SQLite database files to look for
    sqlite_files = [
        'web_crawler.db',
        'url_history.db', 
        'queue_manager.db',
        'summaries.db',
        '*.db',  # Any other .db files
        '*.db-journal',  # SQLite journal files
        '*.db-wal',  # SQLite WAL files
        '*.db-shm'  # SQLite shared memory files
    ]
    
    print(f"Checking for SQLite files in {data_dir}")
    
    if not os.path.exists(data_dir):
        print(f"Data directory {data_dir} does not exist")
        return
    
    removed_files = []
    
    for pattern in sqlite_files:
        # Search for files matching the pattern
        search_pattern = os.path.join(data_dir, pattern)
        matching_files = glob.glob(search_pattern)
        
        for file_path in matching_files:
            if os.path.isfile(file_path):
                try:
                    # Create backup before removing
                    backup_path = file_path + '.backup'
                    shutil.copy2(file_path, backup_path)
                    print(f"Created backup: {backup_path}")
                    
                    # Remove the original file
                    os.remove(file_path)
                    removed_files.append(file_path)
                    print(f"Removed: {file_path}")
                    
                except Exception as e:
                    print(f"Error removing {file_path}: {e}")
    
    if removed_files:
        print(f"\nRemoved {len(removed_files)} SQLite files:")
        for file_path in removed_files:
            print(f"  - {file_path}")
        print("\nBackup files have been created with .backup extension")
    else:
        print("No SQLite files found to remove")

if __name__ == "__main__":
    cleanup_sqlite_files() 