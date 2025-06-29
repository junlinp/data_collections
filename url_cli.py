#!/usr/bin/env python3
"""
URL History Command Line Interface
A tool to manage and query the URL history database
"""

import argparse
import sys
from url_manager import URLManager
from crawler_logic import WebCrawler
from datetime import datetime, timedelta
import json

def format_timestamp(timestamp):
    """Format timestamp for display"""
    if timestamp:
        return datetime.fromisoformat(timestamp).strftime('%Y-%m-%d %H:%M:%S')
    return 'N/A'

def display_url_info(url_info):
    """Display URL information in a formatted way"""
    print(f"\nURL: {url_info['url']}")
    print(f"Domain: {url_info['domain']}")
    print(f"Visit Count: {url_info['visit_count']}")
    print(f"Crawl Depth: {url_info['crawl_depth']}")
    print(f"Last Visited: {format_timestamp(url_info['last_visited'])}")
    print(f"First Visited: {format_timestamp(url_info['first_visited'])}")
    
    if url_info['avg_response_time']:
        print(f"Avg Response Time: {url_info['avg_response_time']:.2f}s")
    if url_info['status_code']:
        print(f"Status Code: {url_info['status_code']}")
    if url_info['content_length']:
        print(f"Content Length: {url_info['content_length']} bytes")
    
    if url_info['metadata']:
        print("Metadata:")
        for key, value in url_info['metadata'].items():
            print(f"  {key}: {value}")

def display_stats(stats):
    """Display database statistics"""
    print("\n=== URL History Statistics ===")
    print(f"Total URLs: {stats['total_urls']}")
    print(f"Total Domains: {stats['total_domains']}")
    print(f"Total Visits: {stats['total_visits']}")
    print(f"Average Response Time: {stats['avg_response_time']:.2f}s")
    print(f"Earliest Visit: {format_timestamp(stats['earliest_visit'])}")
    print(f"Latest Visit: {format_timestamp(stats['latest_visit'])}")

def display_queue_state(crawler):
    """Display current crawler queue state"""
    queue_state = crawler.get_queue_state()
    
    print("\n=== Crawler Queue State ===")
    print(f"Total URLs: {queue_state['total_urls']}")
    print(f"Queued URLs: {queue_state['queued_urls']}")
    print(f"Processing URLs: {queue_state['processing_urls']}")
    print(f"Completed URLs: {queue_state['completed_urls']}")
    print(f"Failed URLs: {queue_state['failed_urls']}")
    
    if queue_state['current_urls']:
        print(f"\nCurrently Processing ({len(queue_state['current_urls'])} threads):")
        for url in queue_state['current_urls']:
            print(f"  - {url}")
    
    if queue_state['start_time']:
        print(f"\nStarted: {queue_state['start_time']}")
    
    if queue_state['estimated_completion']:
        estimated_time = datetime.fromtimestamp(queue_state['estimated_completion'])
        print(f"Estimated Completion: {estimated_time.strftime('%Y-%m-%d %H:%M:%S')}")
    
    if queue_state['completed_urls'] > 0 and queue_state['total_urls'] > 0:
        progress = (queue_state['completed_urls'] / queue_state['total_urls']) * 100
        print(f"\nProgress: {queue_state['completed_urls']}/{queue_state['total_urls']} ({progress:.1f}%)")
        
        # Simple progress bar
        bar_length = 30
        filled_length = int(bar_length * queue_state['completed_urls'] // queue_state['total_urls'])
        bar = '█' * filled_length + '░' * (bar_length - filled_length)
        print(f"[{bar}]")
    
    if queue_state['errors']:
        print(f"\nRecent Errors ({len(queue_state['errors'])}):")
        for error in queue_state['errors'][-5:]:  # Show last 5 errors
            print(f"  - {error}")

def main():
    parser = argparse.ArgumentParser(description='URL History Management CLI')
    parser.add_argument('--db', default='url_history.db', help='Database file path')
    parser.add_argument('--content-db', default='web_crawler.db', help='Content database file path')
    
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Crawl command
    crawl_parser = subparsers.add_parser('crawl', help='Start crawling a website')
    crawl_parser.add_argument('url', help='URL to crawl')
    
    # Stats command
    stats_parser = subparsers.add_parser('stats', help='Show URL history statistics')
    
    # Recent command
    recent_parser = subparsers.add_parser('recent', help='Show recently visited URLs')
    recent_parser.add_argument('--hours', type=int, default=24, help='Hours to look back (default: 24)')
    recent_parser.add_argument('--limit', type=int, default=20, help='Number of URLs to show (default: 20)')
    
    # Most visited command
    most_visited_parser = subparsers.add_parser('most-visited', help='Show most frequently visited URLs')
    most_visited_parser.add_argument('--limit', type=int, default=10, help='Number of URLs to show (default: 10)')
    
    # URL info command
    url_info_parser = subparsers.add_parser('url-info', help='Get information about a specific URL')
    url_info_parser.add_argument('url', help='URL to get information for')
    
    # Check recent command
    check_recent_parser = subparsers.add_parser('check-recent', help='Check if URL was recently visited')
    check_recent_parser.add_argument('url', help='URL to check')
    check_recent_parser.add_argument('--hours', type=int, default=24, help='Hours to look back (default: 24)')
    
    # Export command
    export_parser = subparsers.add_parser('export', help='Export URL history to JSON')
    export_parser.add_argument('--output', default='url_history.json', help='Output file path')
    export_parser.add_argument('--hours', type=int, help='Only export URLs visited within specified hours')
    
    # Queue state command
    queue_parser = subparsers.add_parser('queue', help='Global queue management')
    queue_subparsers = queue_parser.add_subparsers(dest='queue_command', help='Queue commands')
    
    # Queue status command
    queue_status_parser = queue_subparsers.add_parser('status', help='Show global queue status')
    
    # Queue list command
    queue_list_parser = queue_subparsers.add_parser('list', help='List pending URLs in global queue')
    queue_list_parser.add_argument('--limit', type=int, default=50, help='Number of URLs to show (default: 50)')
    queue_list_parser.add_argument('--base-url', help='Filter by base URL domain')
    queue_list_parser.add_argument('--format', choices=['table', 'json'], default='table', help='Output format (default: table)')
    
    # Queue clear command
    queue_clear_parser = queue_subparsers.add_parser('clear', help='Clear global queue')
    queue_clear_parser.add_argument('--base-url', help='Clear only URLs from specific base URL domain')
    queue_clear_parser.add_argument('--confirm', action='store_true', help='Skip confirmation prompt')
    
    # HTML content command
    html_parser = subparsers.add_parser('html', help='View HTML content for a URL')
    html_parser.add_argument('url', help='URL to get HTML content for')
    html_parser.add_argument('--save', help='Save HTML content to file')
    
    # List content command
    content_parser = subparsers.add_parser('content', help='List all crawled content')
    content_parser.add_argument('--limit', type=int, default=50, help='Number of entries to show (default: 50)')
    content_parser.add_argument('--format', choices=['table', 'json'], default='table', help='Output format (default: table)')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    # Initialize URL manager
    url_manager = URLManager(args.db)
    
    # Initialize crawler for queue state and HTML content
    crawler = WebCrawler(args.content_db, args.db)
    
    try:
        if args.command == 'crawl':
            print(f"Starting unlimited single-threaded crawl of: {args.url}")
            print("This will crawl ALL pages on the website without depth or page restrictions.")
            print("Press Ctrl+C to stop the crawl.")
            
            try:
                result = crawler.crawl_website(args.url)
                print("\nCrawling completed!")
                print(f"  Total URLs discovered: {result['total_visited']}")
                print(f"  Successfully crawled: {result['completed_urls']}")
                print(f"  Failed URLs: {result['failed_urls']}")
                if result['errors']:
                    print(f"  Errors: {len(result['errors'])}")
                    for error in result['errors'][-5:]:  # Show last 5 errors
                        print(f"    - {error}")
            except KeyboardInterrupt:
                print("\nCrawl interrupted by user.")
                crawler.stop_crawling()
            except Exception as e:
                print(f"Error during crawling: {e}")
            
        elif args.command == 'stats':
            stats = url_manager.get_database_stats()
            print("URL History Statistics:")
            print(f"  Total URLs: {stats['total_urls']}")
            print(f"  Total Domains: {stats['total_domains']}")
            print(f"  Total Visits: {stats['total_visits']}")
            print(f"  Average Response Time: {stats['avg_response_time']:.2f}s" if stats['avg_response_time'] else "  Average Response Time: N/A")
            print(f"  Earliest Visit: {stats['earliest_visit']}" if stats['earliest_visit'] else "  Earliest Visit: N/A")
            print(f"  Latest Visit: {stats['latest_visit']}" if stats['latest_visit'] else "  Latest Visit: N/A")
            
        elif args.command == 'recent':
            recent_urls = url_manager.get_recent_urls(args.hours, args.limit)
            print(f"Recently Visited URLs (Last {args.hours} hours):")
            if recent_urls:
                print(f"{'URL':<50} {'Domain':<20} {'Visits':<8} {'Depth':<6} {'Last Visited'}")
                print("-" * 100)
                for url_info in recent_urls:
                    print(f"{url_info['url']:<50} {url_info['domain']:<20} {url_info['visit_count']:<8} {url_info['crawl_depth']:<6} {url_info['last_visited']}")
            else:
                print("No URLs visited in the specified time period.")
                
        elif args.command == 'most-visited':
            most_visited = url_manager.get_most_visited_urls(args.limit)
            print(f"Most Frequently Visited URLs:")
            if most_visited:
                print(f"{'URL':<50} {'Domain':<20} {'Visits':<8} {'Last Visited'}")
                print("-" * 90)
                for url_info in most_visited:
                    print(f"{url_info['url']:<50} {url_info['domain']:<20} {url_info['visit_count']:<8} {url_info['last_visited']}")
            else:
                print("No URL history available.")
                
        elif args.command == 'url-info':
            info = url_manager.get_url_info(args.url)
            if info:
                print(f"URL Information for: {args.url}")
                print(f"  Domain: {info['domain']}")
                print(f"  Visit Count: {info['visit_count']}")
                print(f"  Crawl Depth: {info['crawl_depth']}")
                print(f"  First Visited: {info['first_visited']}")
                print(f"  Last Visited: {info['last_visited']}")
                print(f"  Average Response Time: {info['avg_response_time']:.2f}s" if info['avg_response_time'] else "  Average Response Time: N/A")
                print(f"  Status Codes: {info['status_codes']}")
                if info['metadata']:
                    print(f"  Metadata: {json.dumps(info['metadata'], indent=2)}")
            else:
                print(f"URL not found in history: {args.url}")
                
        elif args.command == 'check-recent':
            is_recent = url_manager.is_recently_visited(args.url, args.hours)
            if is_recent:
                print(f"✓ URL was visited within the last {args.hours} hours: {args.url}")
            else:
                print(f"✗ URL was not visited within the last {args.hours} hours: {args.url}")
                
        elif args.command == 'export':
            # Get all URLs or recent URLs
            if args.hours:
                # Get recent URLs within specified hours
                recent_urls = url_manager.get_recent_urls(args.hours, 10000)  # Large limit to get all
                data = {
                    'export_time': datetime.now().isoformat(),
                    'hours_back': args.hours,
                    'urls': recent_urls
                }
            else:
                # Get all URLs (this would need to be implemented in URLManager)
                print("Exporting all URLs not yet implemented. Use --hours to export recent URLs.")
                return
            
            with open(args.output, 'w') as f:
                json.dump(data, f, indent=2, default=str)
            print(f"Exported {len(data['urls'])} URLs to {args.output}")
            
        elif args.command == 'queue':
            if not args.queue_command:
                queue_parser.print_help()
                return
                
            if args.queue_command == 'status':
                global_queue_state = crawler.get_global_queue_state()
                if global_queue_state:
                    print("Global Queue Status:")
                    print(f"  Total URLs: {global_queue_state.get('total_urls', 0)}")
                    print(f"  Pending URLs: {global_queue_state.get('queued_urls', 0)}")
                    print(f"  Processing URLs: {global_queue_state.get('processing_urls', 0)}")
                    print(f"  Completed URLs: {global_queue_state.get('completed_urls', 0)}")
                    print(f"  Failed URLs: {global_queue_state.get('failed_urls', 0)}")
                    print(f"  Last Updated: {global_queue_state.get('last_updated', 'N/A')}")
                else:
                    print("No global queue data available.")
                    
            elif args.queue_command == 'list':
                pending_urls = crawler.get_pending_urls(args.base_url, args.limit)
                if not pending_urls:
                    print("No pending URLs in the global queue.")
                    return
                    
                if args.format == 'json':
                    # Convert to JSON-serializable format
                    json_data = []
                    for url_info in pending_urls:
                        json_data.append({
                            'url': url_info[0],
                            'depth': url_info[1],
                            'priority': url_info[2],
                            'added_at': url_info[3]
                        })
                    print(json.dumps(json_data, indent=2, default=str))
                else:
                    print(f"Pending URLs in Global Queue (showing {len(pending_urls)} entries):")
                    if args.base_url:
                        print(f"Filtered by base URL: {args.base_url}")
                    print(f"{'URL':<50} {'Depth':<6} {'Priority':<10} {'Added At'}")
                    print("-" * 80)
                    for url_info in pending_urls:
                        url = url_info[0][:49] + "..." if len(url_info[0]) > 50 else url_info[0]
                        depth = url_info[1]
                        priority = url_info[2]
                        added_at = url_info[3]
                        
                        # Priority label
                        if priority >= 10:
                            priority_label = "High"
                        elif priority >= 5:
                            priority_label = "Medium"
                        else:
                            priority_label = "Low"
                        
                        print(f"{url:<50} {depth:<6} {priority_label:<10} {added_at}")
                        
            elif args.queue_command == 'clear':
                if not args.confirm:
                    if args.base_url:
                        confirm_msg = f"Are you sure you want to clear the queue for {args.base_url}? (y/N): "
                    else:
                        confirm_msg = "Are you sure you want to clear ALL queues? This cannot be undone! (y/N): "
                    
                    response = input(confirm_msg).strip().lower()
                    if response not in ['y', 'yes']:
                        print("Operation cancelled.")
                        return
                
                try:
                    success = crawler.clear_global_queue(args.base_url)
                    if success:
                        if args.base_url:
                            print(f"Queue cleared successfully for {args.base_url}")
                        else:
                            print("All queues cleared successfully")
                    else:
                        print("Failed to clear queue")
                except Exception as e:
                    print(f"Error clearing queue: {e}")
            
        elif args.command == 'html':
            html_content = crawler.get_html_content_by_url(args.url)
            if html_content:
                if args.save:
                    with open(args.save, 'w', encoding='utf-8') as f:
                        f.write(html_content)
                    print(f"HTML content saved to: {args.save}")
                else:
                    print(f"HTML Content for: {args.url}")
                    print(f"Size: {len(html_content)} characters")
                    print("-" * 80)
                    print(html_content[:2000] + "..." if len(html_content) > 2000 else html_content)
            else:
                print(f"HTML content not found for URL: {args.url}")
                
        elif args.command == 'content':
            content_data = crawler.get_crawled_content_data()
            if not content_data:
                print("No crawled content available.")
                return
                
            # Limit the data
            content_data = content_data[:args.limit]
            
            if args.format == 'json':
                # Convert to JSON-serializable format
                json_data = []
                for row in content_data:
                    json_data.append({
                        'url': row[0],
                        'title': row[1],
                        'content_preview': row[2][:200] + "..." if len(row[2]) > 200 else row[2],
                        'html_size': len(row[3]) if row[3] else 0,
                        'links_count': row[4].count('\n') + 1 if row[4] else 0,
                        'crawl_depth': row[6] or 0,
                        'crawled_at': row[5]
                    })
                print(json.dumps(json_data, indent=2, default=str))
            else:
                print(f"Crawled Content (showing {len(content_data)} entries):")
                print(f"{'URL':<40} {'Title':<30} {'Content':<30} {'HTML':<8} {'Links':<6} {'Depth':<6} {'Crawled At'}")
                print("-" * 130)
                for row in content_data:
                    url = row[0][:39] + "..." if len(row[0]) > 40 else row[0]
                    title = (row[1] or "No title")[:29] + "..." if len(row[1] or "") > 30 else (row[1] or "No title")
                    content = row[2][:29] + "..." if len(row[2]) > 30 else row[2]
                    html_size = f"{len(row[3])}c" if row[3] else "0c"
                    links_count = row[4].count('\n') + 1 if row[4] else 0
                    depth = row[6] or 0
                    crawled_at = row[5]
                    
                    print(f"{url:<40} {title:<30} {content:<30} {html_size:<8} {links_count:<6} {depth:<6} {crawled_at}")
    
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main() 