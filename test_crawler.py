#!/usr/bin/env python3
"""
Test script to verify crawler link extraction
"""

import logging
from crawler_logic import WebCrawler
from bs4 import BeautifulSoup
import requests

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_link_extraction():
    """Test link extraction on a simple website"""
    
    # Test with a simple website
    test_url = "https://httpbin.org/html"
    
    print("🧪 Testing link extraction...")
    print(f"Test URL: {test_url}")
    
    try:
        # Fetch the page
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        response = requests.get(test_url, timeout=10, headers=headers)
        response.raise_for_status()
        
        # Parse HTML
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Test the crawler's link extraction
        crawler = WebCrawler()
        links, discovered = crawler.extract_links(soup, test_url, test_url)
        
        print(f"✅ Found {len(links)} links")
        if links:
            print("Sample links:")
            for i, link in enumerate(links[:5]):
                print(f"  {i+1}. {link}")
        else:
            print("No links found (this is normal for httpbin.org)")
            
    except Exception as e:
        print(f"❌ Error testing link extraction: {e}")

def test_real_website():
    """Test with a real website that has links"""
    
    # Test with a website that has many links
    test_url = "https://example.com"
    
    print(f"\n🧪 Testing with real website: {test_url}")
    
    try:
        # Create crawler
        crawler = WebCrawler(max_workers=2)
        
        # Start a small crawl
        print("Starting small crawl (max 5 pages)...")
        result = crawler.crawl_website(test_url, max_workers=2)
        
        print(f"✅ Crawl completed!")
        print(f"📊 Results:")
        print(f"   - Total visited: {result['total_visited']}")
        print(f"   - Completed: {result['completed_urls']}")
        print(f"   - Failed: {result['failed_urls']}")
        print(f"   - Errors: {len(result['errors'])}")
        
        if result['errors']:
            print("Recent errors:")
            for error in result['errors'][-3:]:
                print(f"   - {error}")
                
    except Exception as e:
        print(f"❌ Error testing real website: {e}")

def test_domain_filtering():
    """Test domain filtering logic"""
    
    print("\n🧪 Testing domain filtering...")
    
    crawler = WebCrawler()
    
    # Test cases
    test_cases = [
        ("https://example.com", "https://example.com/page1", True),
        ("https://example.com", "https://www.example.com/page1", True),
        ("https://www.example.com", "https://example.com/page1", True),
        ("https://example.com", "https://other.com/page1", False),
        ("https://example.com", "https://sub.example.com/page1", True),
    ]
    
    for base_url, link_url, expected in test_cases:
        result = crawler.is_same_domain(base_url, link_url)
        status = "✅" if result == expected else "❌"
        print(f"{status} {base_url} vs {link_url} -> {result} (expected: {expected})")

def main():
    """Main test function"""
    print("=" * 60)
    print("🧪 Crawler Link Extraction Test")
    print("=" * 60)
    
    # Test 1: Domain filtering
    test_domain_filtering()
    
    # Test 2: Link extraction
    test_link_extraction()
    
    # Test 3: Real website crawl
    test_real_website()
    
    print("=" * 60)
    print("🧪 Test completed")

if __name__ == "__main__":
    main() 