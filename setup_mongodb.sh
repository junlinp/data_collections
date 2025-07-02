#!/bin/bash

# Setup script for MongoDB data directory
# This script ensures the MongoDB data directory exists with proper permissions

echo "Setting up MongoDB data directory..."

# Create MongoDB data directory if it doesn't exist
MONGODB_DATA_DIR="/mnt/rbd0/crawler_data/mongodb"

if [ ! -d "$MONGODB_DATA_DIR" ]; then
    echo "Creating MongoDB data directory: $MONGODB_DATA_DIR"
    mkdir -p "$MONGODB_DATA_DIR"
else
    echo "MongoDB data directory already exists: $MONGODB_DATA_DIR"
fi

# Set proper permissions
echo "Setting permissions for MongoDB data directory..."
chmod 755 "$MONGODB_DATA_DIR"

# Create parent directory if it doesn't exist
PARENT_DIR="/mnt/rbd0/crawler_data"
if [ ! -d "$PARENT_DIR" ]; then
    echo "Creating parent directory: $PARENT_DIR"
    mkdir -p "$PARENT_DIR"
    chmod 755 "$PARENT_DIR"
fi

echo "MongoDB setup completed successfully!"
echo "Data directory: $MONGODB_DATA_DIR"
echo "You can now start the services with: docker-compose up -d" 