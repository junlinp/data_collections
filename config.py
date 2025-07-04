"""
Configuration settings for the web crawler application
Centralized configuration for better maintainability
"""

import os

class Config:
    """Base configuration class"""
    
    # Database settings
    CONTENT_DB_PATH = os.getenv('CONTENT_DB_PATH', 'web_crawler.db')
    URL_HISTORY_DB_PATH = os.getenv('URL_HISTORY_DB_PATH', 'url_history.db')
    
    # Flask settings
    SECRET_KEY = os.getenv('SECRET_KEY', 'your-secret-key-change-this')
    DEBUG = os.getenv('DEBUG', 'True').lower() == 'true'
    HOST = os.getenv('HOST', '127.0.0.1')
    PORT = int(os.getenv('PORT', 5000))
    
    # Crawler settings
    DEFAULT_MAX_PAGES = int(os.getenv('DEFAULT_MAX_PAGES', 50))
    MAX_PAGES_LIMIT = int(os.getenv('MAX_PAGES_LIMIT', 200))
    
    # Request settings
    REQUEST_TIMEOUT = int(os.getenv('REQUEST_TIMEOUT', 10))
    REQUEST_DELAY = float(os.getenv('REQUEST_DELAY', 1.0))
    USER_AGENT = os.getenv('USER_AGENT', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')
    
    # Content settings
    MAX_CONTENT_LENGTH = int(os.getenv('MAX_CONTENT_LENGTH', 10000))
    CONTENT_PREVIEW_LENGTH = int(os.getenv('CONTENT_PREVIEW_LENGTH', 100))
    
    # URL History settings
    DEFAULT_RECENT_HOURS = int(os.getenv('DEFAULT_RECENT_HOURS', 24))
    DEFAULT_RECENT_LIMIT = int(os.getenv('DEFAULT_RECENT_LIMIT', 20))
    DEFAULT_MOST_VISITED_LIMIT = int(os.getenv('DEFAULT_MOST_VISITED_LIMIT', 10))
    
    # Cleanup settings
    DEFAULT_CLEANUP_DAYS = int(os.getenv('DEFAULT_CLEANUP_DAYS', 30))
    
    # API settings
    API_RATE_LIMIT = os.getenv('API_RATE_LIMIT', '100 per minute')
    
    @classmethod
    def get_crawler_settings(cls):
        """Get crawler-specific settings"""
        return {
            'max_pages': cls.DEFAULT_MAX_PAGES,
            'timeout': cls.REQUEST_TIMEOUT,
            'delay': cls.REQUEST_DELAY,
            'user_agent': cls.USER_AGENT,
            'max_content_length': cls.MAX_CONTENT_LENGTH
        }
    
    @classmethod
    def get_flask_settings(cls):
        """Get Flask-specific settings"""
        return {
            'debug': cls.DEBUG,
            'host': cls.HOST,
            'port': cls.PORT,
            'secret_key': cls.SECRET_KEY
        }

class DevelopmentConfig(Config):
    """Development configuration"""
    DEBUG = True
    DEFAULT_MAX_PAGES = 20
    REQUEST_DELAY = 0.5

class ProductionConfig(Config):
    """Production configuration"""
    DEBUG = False
    DEFAULT_MAX_PAGES = 100
    REQUEST_DELAY = 2.0
    HOST = '0.0.0.0'

class TestingConfig(Config):
    """Testing configuration"""
    DEBUG = True
    CONTENT_DB_PATH = 'test_web_crawler.db'
    URL_HISTORY_DB_PATH = 'test_url_history.db'
    DEFAULT_MAX_PAGES = 5
    REQUEST_DELAY = 0.1

# Configuration mapping
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}

def get_config(config_name=None):
    """Get configuration based on environment"""
    if config_name is None:
        config_name = os.getenv('FLASK_ENV', 'default')
    return config.get(config_name, config['default']) 