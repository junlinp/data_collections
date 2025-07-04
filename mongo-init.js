// MongoDB initialization script for web crawler
// This script runs when the MongoDB container starts for the first time

// Switch to the crawler database
db = db.getSiblingDB('crawler_db');

// Create collections with proper indexes
db.createCollection('web_content');
db.createCollection('url_history');
db.createCollection('summaries');

// Create indexes for better performance
db.web_content.createIndex({ "url": 1 }, { unique: true });
db.web_content.createIndex({ "created_at": 1 });

db.url_history.createIndex({ "url": 1 });
db.url_history.createIndex({ "created_at": 1 });
db.url_history.createIndex({ "status": 1 });

db.summaries.createIndex({ "url": 1 }, { unique: true });
db.summaries.createIndex({ "created_at": 1 });
db.summaries.createIndex({ "sentiment": 1 });

// Create a user for the crawler application
db.createUser({
  user: "crawler_user",
  pwd: "crawler_password",
  roles: [
    { role: "readWrite", db: "crawler_db" }
  ]
});

print("MongoDB initialization completed successfully!"); 