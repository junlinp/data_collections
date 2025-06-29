import os
import sqlite3
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

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)

class LLMProcessor:
    def __init__(self, content_db_path, summary_db_path):
        self.content_db_path = content_db_path
        self.summary_db_path = summary_db_path
        self.local_llm_url = os.getenv('LOCAL_LLM_URL', 'http://localhost:11434')
        self.local_llm_model = os.getenv('LOCAL_LLM_MODEL', 'deepseek-r1:latest')
        self.processing_in_progress = False
        self.init_summary_database()
    
    def init_summary_database(self):
        """Initialize the summary database"""
        conn = sqlite3.connect(self.summary_db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS summaries (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                url TEXT UNIQUE NOT NULL,
                title TEXT,
                summary TEXT NOT NULL,
                key_points TEXT,
                sentiment TEXT,
                word_count INTEGER,
                processing_time REAL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        conn.commit()
        conn.close()
        logger.info(f"Summary database initialized at {self.summary_db_path}")
    
    def get_unprocessed_urls(self):
        """Get URLs that haven't been processed yet"""
        try:
            # Connect to content database
            content_conn = sqlite3.connect(self.content_db_path)
            content_cursor = content_conn.cursor()
            
            # Connect to summary database
            summary_conn = sqlite3.connect(self.summary_db_path)
            summary_cursor = summary_conn.cursor()
            
            # Get all URLs from content database (using correct table name)
            content_cursor.execute('SELECT url, title, html_content FROM crawled_content')
            all_urls = content_cursor.fetchall()
            
            # Get already processed URLs
            summary_cursor.execute('SELECT url FROM summaries')
            processed_urls = {row[0] for row in summary_cursor.fetchall()}
            
            # Filter unprocessed URLs
            unprocessed = []
            for url, title, html_content in all_urls:
                if url not in processed_urls and html_content:
                    unprocessed.append((url, title, html_content))
            
            content_conn.close()
            summary_conn.close()
            
            return unprocessed
            
        except Exception as e:
            logger.error(f"Error getting unprocessed URLs: {e}")
            return []
    
    def extract_text_from_html(self, html_content):
        """Extract clean text from HTML content"""
        try:
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # Remove script and style elements
            for script in soup(["script", "style"]):
                script.decompose()
            
            # Get text and clean it
            text = soup.get_text()
            lines = (line.strip() for line in text.splitlines())
            chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
            text = ' '.join(chunk for chunk in chunks if chunk)
            
            return text
        except Exception as e:
            logger.error(f"Error extracting text from HTML: {e}")
            return ""
    
    def generate_summary_with_local_llm(self, text, url, title):
        """Generate summary using local LLM server (Ollama)"""
        try:
            # Truncate text if too long
            max_chars = 4000  # Conservative limit for local models
            if len(text) > max_chars:
                text = text[:max_chars] + "..."
            
            prompt = f"""
            Please analyze the following web content and provide a comprehensive summary.
            
            URL: {url}
            Title: {title}
            
            Content:
            {text}
            
            Please provide a structured response with:
            1. A concise summary (2-3 paragraphs)
            2. Key points (bullet points)
            3. Overall sentiment (positive, negative, neutral)
            4. Estimated word count of the original content
            
            Format your response as JSON:
            {{
                "summary": "detailed summary here",
                "key_points": ["point 1", "point 2", "point 3"],
                "sentiment": "positive/negative/neutral",
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
                return self._fallback_summary(text, url, title)
            
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
                    return parsed_result
                else:
                    # Fallback: create structured response
                    return self._fallback_summary(text, url, title, content)
            except json.JSONDecodeError:
                # Fallback: create structured response
                return self._fallback_summary(text, url, title, content)
                
        except requests.exceptions.RequestException as e:
            logger.error(f"Error connecting to local LLM server for {url}: {e}")
            return self._fallback_summary(text, url, title)
        except Exception as e:
            logger.error(f"Error generating summary for {url}: {e}")
            return self._fallback_summary(text, url, title)
    
    def _fallback_summary(self, text, url, title, llm_response=""):
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
            
            # Extract key points (simple approach)
            sentences = text.split('.')
            key_points = []
            for sentence in sentences[:5]:  # Take first 5 sentences as key points
                sentence = sentence.strip()
                if len(sentence) > 20:  # Only meaningful sentences
                    key_points.append(sentence[:100] + "..." if len(sentence) > 100 else sentence)
            
            # Create summary
            if llm_response:
                summary = llm_response
            else:
                summary = f"Content from {url} with title '{title}'. The page contains {word_count} words with {sentiment} sentiment. Key topics include: " + ", ".join(key_points[:3])
            
            return {
                "summary": summary,
                "key_points": key_points[:5],
                "sentiment": sentiment,
                "word_count": word_count
            }
            
        except Exception as e:
            logger.error(f"Error in fallback summary: {e}")
            return {
                "summary": f"Error processing content from {url}: {str(e)}",
                "key_points": [],
                "sentiment": "neutral",
                "word_count": 0
            }
    
    def save_summary(self, url, title, summary_data, processing_time):
        """Save summary to database"""
        try:
            conn = sqlite3.connect(self.summary_db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT OR REPLACE INTO summaries 
                (url, title, summary, key_points, sentiment, word_count, processing_time, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                url,
                title,
                summary_data.get('summary', ''),
                '\n'.join(summary_data.get('key_points', [])),
                summary_data.get('sentiment', 'neutral'),
                summary_data.get('word_count', 0),
                processing_time,
                datetime.now().isoformat()
            ))
            
            conn.commit()
            conn.close()
            logger.info(f"Summary saved for {url}")
            
        except Exception as e:
            logger.error(f"Error saving summary for {url}: {e}")
    
    def process_url(self, url, title, html_content):
        """Process a single URL"""
        start_time = time.time()
        
        try:
            # Extract text from HTML
            text = self.extract_text_from_html(html_content)
            if not text:
                logger.warning(f"No text extracted from {url}")
                return False
            
            # Generate summary with local LLM
            summary_data = self.generate_summary_with_local_llm(text, url, title)
            
            # Calculate processing time
            processing_time = time.time() - start_time
            
            # Save summary
            self.save_summary(url, title, summary_data, processing_time)
            
            return True
            
        except Exception as e:
            logger.error(f"Error processing {url}: {e}")
            return False
    
    def process_all_unprocessed(self):
        """Process all unprocessed URLs"""
        if self.processing_in_progress:
            logger.warning("Processing already in progress")
            return
        
        self.processing_in_progress = True
        
        try:
            unprocessed = self.get_unprocessed_urls()
            logger.info(f"Found {len(unprocessed)} unprocessed URLs")
            
            if not unprocessed:
                logger.info("No unprocessed URLs found")
                return
            
            processed_count = 0
            for url, title, html_content in unprocessed:
                if self.process_url(url, title, html_content):
                    processed_count += 1
                    logger.info(f"Processed {processed_count}/{len(unprocessed)}: {url}")
                
                # Add delay to avoid overwhelming the local LLM
                time.sleep(2)
            
            logger.info(f"Processing completed. {processed_count}/{len(unprocessed)} URLs processed successfully")
            
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

# Initialize processor
content_db_path = os.getenv('CONTENT_DB_PATH', '/app/data/web_crawler.db')
summary_db_path = os.getenv('SUMMARY_DB_PATH', '/app/data/summaries.db')
processor = LLMProcessor(content_db_path, summary_db_path)

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
        # Get content from database
        conn = sqlite3.connect(processor.content_db_path)
        cursor = conn.cursor()
        cursor.execute('SELECT title, html_content FROM crawled_content WHERE url = ?', (url,))
        result = cursor.fetchone()
        conn.close()
        
        if not result:
            return jsonify({
                'success': False,
                'error': 'URL not found in database'
            }), 404
        
        title, html_content = result
        
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
    """Get processing status"""
    unprocessed = processor.get_unprocessed_urls()
    
    conn = sqlite3.connect(processor.summary_db_path)
    cursor = conn.cursor()
    cursor.execute('SELECT COUNT(*) FROM summaries')
    processed_count = cursor.fetchone()[0]
    conn.close()
    
    llm_available = processor.check_local_llm_status()
    
    return jsonify({
        'success': True,
        'data': {
            'processing_in_progress': processor.processing_in_progress,
            'unprocessed_count': len(unprocessed),
            'processed_count': processed_count,
            'total_count': len(unprocessed) + processed_count,
            'local_llm_available': llm_available,
            'local_llm_url': processor.local_llm_url,
            'local_llm_model': processor.local_llm_model
        }
    })

@app.route("/api/summaries", methods=["GET"])
def get_summaries():
    """Get all summaries with pagination"""
    page = int(request.args.get('page', 1))
    per_page = int(request.args.get('per_page', 20))
    offset = (page - 1) * per_page
    
    try:
        conn = sqlite3.connect(processor.summary_db_path)
        cursor = conn.cursor()
        
        # Get total count
        cursor.execute('SELECT COUNT(*) FROM summaries')
        total_count = cursor.fetchone()[0]
        
        # Get summaries
        cursor.execute('''
            SELECT url, title, summary, key_points, sentiment, word_count, 
                   processing_time, created_at, updated_at
            FROM summaries 
            ORDER BY created_at DESC 
            LIMIT ? OFFSET ?
        ''', (per_page, offset))
        
        summaries = []
        for row in cursor.fetchall():
            summaries.append({
                'url': row[0],
                'title': row[1],
                'summary': row[2],
                'key_points': row[3].split('\n') if row[3] else [],
                'sentiment': row[4],
                'word_count': row[5],
                'processing_time': row[6],
                'created_at': row[7],
                'updated_at': row[8]
            })
        
        conn.close()
        
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
        conn = sqlite3.connect(processor.summary_db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT url, title, summary, key_points, sentiment, word_count, 
                   processing_time, created_at, updated_at
            FROM summaries 
            WHERE url = ?
        ''', (url,))
        
        result = cursor.fetchone()
        conn.close()
        
        if not result:
            return jsonify({
                'success': False,
                'error': 'Summary not found'
            }), 404
        
        summary = {
            'url': result[0],
            'title': result[1],
            'summary': result[2],
            'key_points': result[3].split('\n') if result[3] else [],
            'sentiment': result[4],
            'word_count': result[5],
            'processing_time': result[6],
            'created_at': result[7],
            'updated_at': result[8]
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