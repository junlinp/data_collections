import os
import logging
import time
import threading
import json
from datetime import datetime
from flask import Flask, request, jsonify
from flask_cors import CORS
import requests
from bs4 import BeautifulSoup
from dotenv import load_dotenv
import re
from mongo_utils import get_mongo_manager

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)

class LLMProcessor:
    def __init__(self):
        self.local_llm_url = os.getenv('LOCAL_LLM_URL', 'http://localhost:11434')
        self.local_llm_model = os.getenv('LOCAL_LLM_MODEL', 'deepseek-r1:latest')
        self.processing_in_progress = False
        self.init_summary_database()
    
    def init_summary_database(self):
        """Initialize the MongoDB connection"""
        try:
            # Initialize MongoDB manager
            self.mongo_manager = get_mongo_manager()
            logger.info("MongoDB connection initialized for LLM processor")
        except Exception as e:
            logger.error(f"Error initializing MongoDB: {e}")
            raise
    
    def get_unprocessed_urls(self, limit=1000, offset=0):
        """Get URLs that haven't been processed yet - with pagination support"""
        try:
            logger.info(f"[get_unprocessed_urls] Getting unprocessed URLs from MongoDB (limit={limit}, offset={offset})")
            
            # Get unprocessed URLs from MongoDB
            unprocessed_docs = self.mongo_manager.get_unprocessed_urls(limit=limit)
            logger.info(f"[get_unprocessed_urls] Found {len(unprocessed_docs)} unprocessed URLs from MongoDB")
            
            # Convert to the expected format
            unprocessed = []
            for doc in unprocessed_docs:
                url = doc.get('url')
                title = doc.get('title')
                html_content = doc.get('html_content', '')
                if url and html_content:
                    unprocessed.append((url, title, html_content))
            
            logger.info(f"[get_unprocessed_urls] Returning {len(unprocessed)} unprocessed URLs")
            return unprocessed
            
        except Exception as e:
            logger.error(f"Error getting unprocessed URLs: {e}")
            return []
    
    def get_unprocessed_count(self):
        """Get count of unprocessed URLs without loading all data"""
        try:
            logger.info("[get_unprocessed_count] Getting unprocessed count from MongoDB")
            
            # Get database stats from MongoDB
            stats = self.mongo_manager.get_database_stats()
            
            total_urls = stats.get('web_content_count', 0)
            processed_count = stats.get('summaries_count', 0)
            unprocessed_count = stats.get('unprocessed_count', 0)
            
            logger.info(f"[get_unprocessed_count] Total URLs: {total_urls}, Processed: {processed_count}, Unprocessed: {unprocessed_count}")
            return unprocessed_count
            
        except Exception as e:
            logger.error(f"Error getting unprocessed count: {e}")
            return 0
    
    def extract_text_from_html(self, html_content):
        """Extract article title, date, and main content from HTML using LLM"""
        try:
            # Use LLM to extract structured information from HTML
            extraction_result = self._extract_with_llm(html_content)
            
            if extraction_result:
                text = extraction_result.get('main_content', '')
                article_title = extraction_result.get('article_title')
                article_date = extraction_result.get('publication_date')
                language = extraction_result.get('language', 'english')
                
                # Detect language if not provided by LLM
                if not language or language == 'unknown':
                    language = detect_language(text)
                
                # Only return text if it's English or Chinese
                if language in ['english', 'chinese']:
                    return text, language, article_title, article_date
                else:
                    logger.info(f"Content language not supported: {language}")
                    return "", language, article_title, article_date
            else:
                logger.warning("LLM extraction failed, falling back to basic text extraction")
                return self._fallback_text_extraction(html_content)
                
        except Exception as e:
            logger.error(f"Error extracting text from HTML: {e}")
            return self._fallback_text_extraction(html_content)
    
    def _extract_with_llm(self, html_content):
        """Use LLM to extract structured information from HTML"""
        try:
            # Truncate HTML if too long for LLM
            max_html_chars = 8000  # Conservative limit for HTML processing
            if len(html_content) > max_html_chars:
                html_content = html_content[:max_html_chars] + "..."
            
            prompt = f"""
            Please extract structured information from the following HTML content.
            
            HTML Content:
            {html_content}
            
            Please extract and return the following information in JSON format:
            1. article_title: The main title/headline of the article
            2. publication_date: The publication date (if found)
            3. main_content: The main article content (clean text without HTML tags)
            4. language: The language of the content (english/chinese/unknown)
            
            Focus on:
            - Remove all HTML tags, navigation, ads, and non-content elements
            - Extract only the main article content
            - Preserve the logical flow and structure of the content
            - Identify the most accurate title for the article
            - Find publication dates in various formats
            
            Return as JSON:
            {{
                "article_title": "extracted title",
                "publication_date": "extracted date or null",
                "main_content": "clean main content text",
                "language": "english/chinese/unknown"
            }}
            """
            
            # Prepare request for Ollama
            ollama_request = {
                "model": self.local_llm_model,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": 0.1,  # Low temperature for consistent extraction
                    "top_p": 0.9,
                    "max_tokens": 2000
                }
            }
            
            # Make request to local LLM server
            response = requests.post(
                f"{self.local_llm_url}/api/generate",
                json=ollama_request,
                timeout=60
            )
            
            if response.status_code != 200:
                logger.error(f"Local LLM server error during extraction: {response.status_code}")
                return None
            
            # Parse the response
            result = response.json()
            content = result.get('response', '')
            
            # Try to extract JSON from response
            try:
                # Look for JSON in the response
                start_idx = content.find('{')
                end_idx = content.rfind('}') + 1
                if start_idx != -1 and end_idx != 0:
                    json_str = content[start_idx:end_idx]
                    parsed_result = json.loads(json_str)
                    return parsed_result
                else:
                    logger.warning("No JSON found in LLM response")
                    return None
            except json.JSONDecodeError as e:
                logger.error(f"Error parsing LLM extraction response: {e}")
                return None
                
        except requests.exceptions.RequestException as e:
            logger.error(f"Error connecting to local LLM server for extraction: {e}")
            return None
        except Exception as e:
            logger.error(f"Error in LLM extraction: {e}")
            return None
    
    def _fallback_text_extraction(self, html_content):
        """Fallback text extraction using BeautifulSoup when LLM fails"""
        try:
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # Remove script, style, and navigation elements
            for element in soup(["script", "style", "nav", "header", "footer", "aside", "form"]):
                element.decompose()
            
            # Get text content
            text = soup.get_text(separator=' ', strip=True)
            
            # Clean up whitespace
            lines = (line.strip() for line in text.splitlines())
            chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
            text = ' '.join(chunk for chunk in chunks if chunk)
            
            # Detect language
            language = detect_language(text)
            
            return text, language, None, None
            
        except Exception as e:
            logger.error(f"Error in fallback text extraction: {e}")
            return "", "unknown", None, None
    
    # Removed BeautifulSoup-based extraction methods - now using LLM for extraction
    
    def generate_summary_with_local_llm(self, text, url, title, language="english", article_date=None):
        """Generate summary using local LLM server (Ollama)"""
        try:
            # Truncate text if too long
            max_chars = 4000  # Conservative limit for local models
            if len(text) > max_chars:
                text = text[:max_chars] + "..."
            
            # Use extracted article date if available, otherwise extract from text
            content_date = article_date if article_date else extract_date_from_text(text, url)
            
            # Language-specific prompts
            if language == "chinese":
                prompt = f"""
                请分析以下文章内容并提取关键信息。
                
                URL: {url}
                文章标题: {title}
                发布日期: {content_date if content_date else "未找到日期"}
                
                文章内容:
                {text}
                
                请提供结构化的响应，重点关注：
                1. 文章标题（如果与提供的标题不同，请提供更准确的标题）
                2. 主要内容摘要（2-3段，突出核心观点和重要信息）
                3. 关键要点（列出5-8个最重要的要点）
                4. 发布日期（如果找到）
                5. 文章类型（新闻、博客、技术文档、教程等）
                6. 整体情感倾向（积极、消极、中性）
                7. 目标受众（专业人士、普通读者、开发者等）
                
                请以JSON格式回复：
                {{
                    "article_title": "文章标题",
                    "summary": "详细摘要",
                    "key_points": ["要点1", "要点2", "要点3", "要点4", "要点5"],
                    "publication_date": "发布日期",
                    "article_type": "文章类型",
                    "sentiment": "积极/消极/中性",
                    "target_audience": "目标受众",
                    "word_count": 1234
                }}
                """
            else:
                prompt = f"""
                Please analyze the following article content and extract key information.
                
                URL: {url}
                Article Title: {title}
                Publication Date: {content_date if content_date else "Date not found"}
                
                Article Content:
                {text}
                
                Please provide a structured response focusing on:
                1. Article Title (if different from provided title, provide more accurate title)
                2. Main Content Summary (2-3 paragraphs highlighting core points and important information)
                3. Key Points (list 5-8 most important points)
                4. Publication Date (if found)
                5. Article Type (news, blog, technical documentation, tutorial, etc.)
                6. Overall Sentiment (positive, negative, neutral)
                7. Target Audience (professionals, general readers, developers, etc.)
                
                Format your response as JSON:
                {{
                    "article_title": "article title",
                    "summary": "detailed summary here",
                    "key_points": ["point 1", "point 2", "point 3", "point 4", "point 5"],
                    "publication_date": "publication date",
                    "article_type": "article type",
                    "sentiment": "positive/negative/neutral",
                    "target_audience": "target audience",
                    "word_count": 1234
                }}
                """
            
            # Prepare request for Ollama
            ollama_request = {
                "model": self.local_llm_model,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": 0.3,
                    "top_p": 0.9,
                    "max_tokens": 1000
                }
            }
            
            # Make request to local LLM server
            response = requests.post(
                f"{self.local_llm_url}/api/generate",
                json=ollama_request,
                timeout=60
            )
            
            if response.status_code != 200:
                logger.error(f"Local LLM server error: {response.status_code} - {response.text}")
                return self._fallback_summary(text, url, title, language, content_date)
            
            # Parse the response
            result = response.json()
            content = result.get('response', '')
            logger.info(f"Local LLM response received for {url}")
            
            # Try to extract JSON from response
            try:
                # Look for JSON in the response
                start_idx = content.find('{')
                end_idx = content.rfind('}') + 1
                if start_idx != -1 and end_idx != 0:
                    json_str = content[start_idx:end_idx]
                    parsed_result = json.loads(json_str)
                    # Add language and date if not in response
                    if 'language' not in parsed_result:
                        parsed_result['language'] = language
                    if 'content_date' not in parsed_result:
                        parsed_result['content_date'] = content_date
                    return parsed_result
                else:
                    # Fallback: create structured response
                    return self._fallback_summary(text, url, title, language, content_date, content)
            except json.JSONDecodeError:
                # Fallback: create structured response
                return self._fallback_summary(text, url, title, language, content_date, content)
                
        except requests.exceptions.RequestException as e:
            logger.error(f"Error connecting to local LLM server for {url}: {e}")
            return self._fallback_summary(text, url, title, language, content_date)
        except Exception as e:
            logger.error(f"Error generating summary for {url}: {e}")
            return self._fallback_summary(text, url, title, language, content_date)
    
    def _fallback_summary(self, text, url, title, language, content_date, llm_response=""):
        """Generate a fallback summary when LLM fails"""
        try:
            # Simple text analysis
            words = text.split()
            word_count = len(words)
            
            # Basic sentiment analysis
            positive_words = ['good', 'great', 'excellent', 'amazing', 'wonderful', 'positive', 'success', 'benefit']
            negative_words = ['bad', 'terrible', 'awful', 'negative', 'problem', 'issue', 'fail', 'error']
            
            text_lower = text.lower()
            positive_count = sum(1 for word in positive_words if word in text_lower)
            negative_count = sum(1 for word in negative_words if word in text_lower)
            
            if positive_count > negative_count:
                sentiment = "positive"
            elif negative_count > positive_count:
                sentiment = "negative"
            else:
                sentiment = "neutral"
            
            # Extract key points (improved approach)
            sentences = text.split('.')
            key_points = []
            for sentence in sentences[:8]:  # Take first 8 sentences as key points
                sentence = sentence.strip()
                if len(sentence) > 30:  # Only meaningful sentences
                    key_points.append(sentence[:150] + "..." if len(sentence) > 150 else sentence)
            
            # Determine content type based on URL and content
            content_type = "article"
            if any(word in url.lower() for word in ['news', 'breaking']):
                content_type = "news"
            elif any(word in url.lower() for word in ['report', 'study', 'research']):
                content_type = "report"
            elif any(word in url.lower() for word in ['blog', 'post']):
                content_type = "blog"
            
            # Create summary
            if llm_response:
                summary = llm_response
            else:
                summary = f"Content from {url} with title '{title}'. The page contains {word_count} words with {sentiment} sentiment. Content type: {content_type}. Key topics include: " + ", ".join(key_points[:3])
            
            return {
                "summary": summary,
                "key_points": key_points[:5],
                "sentiment": sentiment,
                "word_count": word_count,
                "language": language,
                "content_date": content_date,
                "content_type": content_type
            }
            
        except Exception as e:
            logger.error(f"Error in fallback summary: {e}")
            return {
                "summary": f"Error processing content from {url}: {str(e)}",
                "key_points": [],
                "sentiment": "neutral",
                "word_count": 0,
                "language": language,
                "content_date": content_date,
                "content_type": "unknown"
            }
    
    def save_summary(self, url, title, summary_data, processing_time):
        """Save summary to MongoDB"""
        try:
            success = self.mongo_manager.save_summary(
                url=url,
                title=title,
                summary=summary_data.get('summary', ''),
                key_points='\n'.join(summary_data.get('key_points', [])),
                sentiment=summary_data.get('sentiment', 'neutral'),
                word_count=summary_data.get('word_count', 0),
                processing_time=processing_time
            )
            
            if success:
                logger.info(f"Summary saved for {url} to MongoDB (language: {summary_data.get('language', 'unknown')})")
            else:
                logger.error(f"Failed to save summary for {url} to MongoDB")
                
        except Exception as e:
            logger.error(f"Error saving summary for {url}: {e}")
    
    def process_url(self, url, title, html_content):
        """Process a single URL"""
        start_time = time.time()
        
        try:
            # Extract text, title, and date from HTML
            text, language, article_title, article_date = self.extract_text_from_html(html_content)
            if not text:
                logger.warning(f"No text extracted from {url}")
                return False
            
            # Only process English or Chinese content
            if language not in ['english', 'chinese']:
                logger.info(f"Skipping {url} - language not supported: {language}")
                return False
            
            # Use extracted article title if available, otherwise use provided title
            final_title = article_title if article_title else title
            
            logger.info(f"Processing {url} - language: {language}, title: {final_title}")
            
            # Generate summary with local LLM
            summary_data = self.generate_summary_with_local_llm(text, url, final_title, language, article_date)
            
            # Calculate processing time
            processing_time = time.time() - start_time
            
            # Save summary
            self.save_summary(url, final_title, summary_data, processing_time)
            
            return True
            
        except Exception as e:
            logger.error(f"Error processing {url}: {e}")
            return False
    
    def process_all_unprocessed(self):
        """Process all unprocessed URLs using pagination"""
        if self.processing_in_progress:
            logger.warning("Processing already in progress")
            return
        
        self.processing_in_progress = True
        
        try:
            batch_size = 100  # Process 100 URLs at a time
            offset = 0
            total_processed = 0
            
            while True:
                logger.info(f"Processing batch: offset={offset}, batch_size={batch_size}")
                unprocessed_batch = self.get_unprocessed_urls(limit=batch_size, offset=offset)
                
                if not unprocessed_batch:
                    logger.info("No more unprocessed URLs found")
                    break
                
                logger.info(f"Found {len(unprocessed_batch)} unprocessed URLs in this batch")
                
                batch_processed = 0
                for url, title, html_content in unprocessed_batch:
                    if self.process_url(url, title, html_content):
                        batch_processed += 1
                        total_processed += 1
                        logger.info(f"Processed {total_processed} total: {url}")
                    
                    # Add delay to avoid overwhelming the local LLM
                    time.sleep(2)
                
                logger.info(f"Batch completed: {batch_processed}/{len(unprocessed_batch)} URLs processed")
                
                # Move to next batch
                offset += batch_size
                
                # Safety check: don't process more than 1000 URLs in one session
                if offset >= 1000:
                    logger.info("Reached safety limit of 1000 URLs per session")
                    break
            
            logger.info(f"Processing completed. {total_processed} URLs processed successfully")
            
        except Exception as e:
            logger.error(f"Error in batch processing: {e}")
        finally:
            self.processing_in_progress = False
    
    def check_local_llm_status(self):
        """Check if local LLM server is available"""
        try:
            response = requests.get(f"{self.local_llm_url}/api/tags", timeout=5)
            return response.status_code == 200
        except Exception as e:
            logger.error(f"Local LLM server not available: {e}")
            return False

def detect_language(text):
    """Detect if text is English or Chinese"""
    if not text:
        return "unknown"
    
    # Count Chinese characters (Unicode ranges for Chinese)
    chinese_chars = len(re.findall(r'[\u4e00-\u9fff]', text))
    # Count English characters
    english_chars = len(re.findall(r'[a-zA-Z]', text))
    
    # If more than 30% of characters are Chinese, consider it Chinese
    total_chars = len(text.replace(' ', ''))
    if total_chars > 0:
        chinese_ratio = chinese_chars / total_chars
        if chinese_ratio > 0.3:
            return "chinese"
        elif english_chars > 10:  # At least some English content
            return "english"
    
    return "unknown"

def extract_date_from_text(text, url):
    """Extract date information from text or URL"""
    # Common date patterns
    date_patterns = [
        r'\b\d{4}-\d{2}-\d{2}\b',  # YYYY-MM-DD
        r'\b\d{2}/\d{2}/\d{4}\b',  # MM/DD/YYYY
        r'\b\d{2}-\d{2}-\d{4}\b',  # MM-DD-YYYY
        r'\b\d{1,2}\s+(?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{4}\b',  # DD Month YYYY
        r'\b(?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2},?\s+\d{4}\b',  # Month DD, YYYY
        r'\b\d{4}年\d{1,2}月\d{1,2}日\b',  # Chinese date format
        r'\b\d{1,2}月\d{1,2}日\b',  # Chinese date without year
    ]
    
    # Check URL first for date patterns
    url_dates = []
    for pattern in date_patterns:
        url_dates.extend(re.findall(pattern, url))
    
    if url_dates:
        return url_dates[0]
    
    # Check text content
    text_dates = []
    for pattern in date_patterns:
        text_dates.extend(re.findall(pattern, text))
    
    if text_dates:
        return text_dates[0]
    
    return None

# Initialize processor (uses MongoDB now)
processor = LLMProcessor()

@app.route("/api/health", methods=["GET"])
def health_check():
    """Health check endpoint"""
    llm_status = processor.check_local_llm_status()
    return jsonify({
        'status': 'healthy' if llm_status else 'llm_unavailable',
        'service': 'llm-processor',
        'local_llm_available': llm_status,
        'local_llm_url': processor.local_llm_url,
        'local_llm_model': processor.local_llm_model,
        'timestamp': time.time()
    })

@app.route("/api/process-all", methods=["POST"])
def process_all():
    """Process all unprocessed URLs"""
    if processor.processing_in_progress:
        return jsonify({
            'success': False,
            'error': 'Processing already in progress'
        }), 400
    
    # Check if local LLM is available
    if not processor.check_local_llm_status():
        return jsonify({
            'success': False,
            'error': 'Local LLM server is not available. Please ensure Ollama is running.'
        }), 503
    
    # Start processing in background thread
    thread = threading.Thread(target=processor.process_all_unprocessed)
    thread.start()
    
    return jsonify({
        'success': True,
        'message': 'Started processing all unprocessed URLs'
    })

@app.route("/api/process-url", methods=["POST"])
def process_single_url():
    """Process a specific URL"""
    data = request.get_json()
    if not data or 'url' not in data:
        return jsonify({
            'success': False,
            'error': 'URL is required'
        }), 400
    
    url = data['url']
    
    try:
        # Get content from MongoDB
        content = processor.mongo_manager.get_web_content(url)
        
        if not content:
            return jsonify({
                'success': False,
                'error': 'URL not found in database'
            }), 404
        
        title = content.get('title', '')
        html_content = content.get('html_content', '')
        
        if not html_content:
            return jsonify({
                'success': False,
                'error': 'No HTML content available for this URL'
            }), 400
        
        # Process the URL
        success = processor.process_url(url, title, html_content)
        
        if success:
            return jsonify({
                'success': True,
                'message': f'Successfully processed {url}'
            })
        else:
            return jsonify({
                'success': False,
                'error': f'Failed to process {url}'
            }), 500
            
    except Exception as e:
        logger.error(f"Error processing URL {url}: {e}")
        return jsonify({
            'success': False,
            'error': f'Error processing URL: {str(e)}'
        }), 500

@app.route("/api/status", methods=["GET"])
def get_status():
    logger.info("/api/status endpoint called")
    try:
        logger.info("About to call processor.get_unprocessed_count()")
        unprocessed_count = processor.get_unprocessed_count()
        logger.info(f"Unprocessed count: {unprocessed_count}")
        logger.info("About to get MongoDB stats")
        stats = processor.mongo_manager.get_database_stats()
        processed_count = stats.get('summaries_count', 0)
        logger.info(f"Processed summaries count: {processed_count}")
        logger.info("About to check LLM availability")
        llm_available = processor.check_local_llm_status()
        logger.info(f"LLM available: {llm_available}")
        response = {
            'success': True,
            'data': {
                'processing_in_progress': processor.processing_in_progress,
                'unprocessed_count': unprocessed_count,
                'processed_count': processed_count,
                'total_count': unprocessed_count + processed_count,
                'local_llm_available': llm_available,
                'local_llm_url': processor.local_llm_url,
                'local_llm_model': processor.local_llm_model
            }
        }
        logger.info(f"/api/status response: {response}")
        return jsonify(response)
    except Exception as e:
        logger.error(f"Exception in /api/status: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route("/api/summaries", methods=["GET"])
def get_summaries():
    """Get all summaries with pagination"""
    page = int(request.args.get('page', 1))
    per_page = int(request.args.get('per_page', 20))
    offset = (page - 1) * per_page
    
    try:
        # Get summaries from MongoDB
        summaries_docs = processor.mongo_manager.get_all_summaries(limit=per_page, skip=offset)
        total_count = processor.mongo_manager.count_summaries()
        
        summaries = []
        for doc in summaries_docs:
            summaries.append({
                'url': doc.get('url'),
                'title': doc.get('title'),
                'summary': doc.get('summary'),
                'key_points': doc.get('key_points', '').split('\n') if doc.get('key_points') else [],
                'sentiment': doc.get('sentiment'),
                'word_count': doc.get('word_count'),
                'processing_time': doc.get('processing_time'),
                'created_at': doc.get('created_at'),
                'updated_at': doc.get('updated_at'),
                'content_date': None,  # Not stored in MongoDB currently
                'language': 'unknown'  # Not stored in MongoDB currently
            })
        
        return jsonify({
            'success': True,
            'data': {
                'summaries': summaries,
                'pagination': {
                    'page': page,
                    'per_page': per_page,
                    'total_count': total_count,
                    'total_pages': (total_count + per_page - 1) // per_page
                }
            }
        })
        
    except Exception as e:
        logger.error(f"Error getting summaries: {e}")
        return jsonify({
            'success': False,
            'error': f'Error getting summaries: {str(e)}'
        }), 500

@app.route("/api/summary/<path:url>", methods=["GET"])
def get_summary_by_url(url):
    """Get summary for a specific URL"""
    try:
        # Get summary from MongoDB
        summary_doc = processor.mongo_manager.get_summary(url)
        
        if not summary_doc:
            return jsonify({
                'success': False,
                'error': 'Summary not found'
            }), 404
        
        summary = {
            'url': summary_doc.get('url'),
            'title': summary_doc.get('title'),
            'summary': summary_doc.get('summary'),
            'key_points': summary_doc.get('key_points', '').split('\n') if summary_doc.get('key_points') else [],
            'sentiment': summary_doc.get('sentiment'),
            'word_count': summary_doc.get('word_count'),
            'processing_time': summary_doc.get('processing_time'),
            'created_at': summary_doc.get('created_at'),
            'updated_at': summary_doc.get('updated_at'),
            'content_date': None,  # Not stored in MongoDB currently
            'language': 'unknown'  # Not stored in MongoDB currently
        }
        
        return jsonify({
            'success': True,
            'data': summary
        })
        
    except Exception as e:
        logger.error(f"Error getting summary for {url}: {e}")
        return jsonify({
            'success': False,
            'error': f'Error getting summary: {str(e)}'
        }), 500

if __name__ == "__main__":
    port = int(os.environ.get('PORT', 5003))
    app.run(host='0.0.0.0', port=port, debug=False) 