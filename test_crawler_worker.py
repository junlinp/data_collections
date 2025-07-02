import unittest
from unittest.mock import MagicMock, patch
from crawler_worker import CrawlerWorker
import json

class TestCrawlerWorkerMetrics(unittest.TestCase):
    @patch('crawler_worker.redis.Redis')
    @patch('crawler_worker.RedisQueueManager')
    def test_metrics_update_on_success(self, MockQueueManager, MockRedis):
        # Setup
        mock_redis = MockRedis.return_value
        mock_queue = MockQueueManager.return_value
        mock_queue.add_url.return_value = True
        mock_queue.queue_length.return_value = 5
        worker = CrawlerWorker(worker_id='test_worker', content_db_path=':memory:')
        worker.redis = mock_redis
        worker.queue = mock_queue
        # Simulate successful response
        worker._extract_title = MagicMock(return_value='Test Title')
        worker._extract_content = MagicMock(return_value='Test Content')
        links = json.dumps(['https://example.com/next'])
        worker._extract_links = MagicMock(return_value=links)
        worker._save_content = MagicMock()
        # Patch requests.Session.get to simulate a 200 response
        class MockResponse:
            status_code = 200
            content = b'<html></html>'
            def __init__(self):
                self.text = '<html></html>'
        with patch.object(worker.session, 'get', return_value=MockResponse()):
            worker._process_url('https://example.com')
        # Check Redis metrics updated
        mock_redis.hincrby.assert_any_call('crawler:metrics', 'completed_urls', 1)
        mock_redis.hset.assert_any_call('crawler:metrics', 'last_crawled_url', 'https://example.com')
        mock_redis.hincrby.assert_any_call('crawler:metrics', 'total_urls', 1)
        mock_redis.hset.assert_any_call('crawler:metrics', 'queue_length', 5)

    @patch('crawler_worker.redis.Redis')
    @patch('crawler_worker.RedisQueueManager')
    def test_metrics_update_on_failure(self, MockQueueManager, MockRedis):
        # Setup
        mock_redis = MockRedis.return_value
        mock_queue = MockQueueManager.return_value
        mock_queue.add_url.return_value = False
        mock_queue.queue_length.return_value = 3
        worker = CrawlerWorker(worker_id='test_worker', content_db_path=':memory:')
        worker.redis = mock_redis
        worker.queue = mock_queue
        # Patch requests.Session.get to simulate a 404 response
        class MockResponse:
            status_code = 404
            content = b''
            def __init__(self):
                self.text = ''
        with patch.object(worker.session, 'get', return_value=MockResponse()):
            worker._process_url('https://example.com/fail')
        # Check Redis metrics updated for failure
        mock_redis.hincrby.assert_any_call('crawler:metrics', 'failed_urls', 1)
        mock_redis.hset.assert_any_call('crawler:metrics', 'queue_length', 3)

if __name__ == '__main__':
    unittest.main() 