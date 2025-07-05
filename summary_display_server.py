import os
import logging
from datetime import datetime
from flask import Flask, render_template, request, jsonify
from flask_cors import CORS
import requests
from mongo_utils import get_mongo_manager

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)

# Configuration
SUMMARY_DB_PATH = os.getenv('SUMMARY_DB_PATH', '/app/data/summaries.db')
LLM_PROCESSOR_URL = os.getenv('LLM_PROCESSOR_URL', 'http://llm-processor:5003')

def get_mongo_manager():
    """Get MongoDB manager instance"""
    return get_mongo_manager()

def get_summaries_with_pagination(page=1, limit=12, search=''):
    """Get summaries with pagination and search from MongoDB"""
    try:
        mongo_manager = get_mongo_manager()
        offset = (page - 1) * limit
        
        # Get summaries from MongoDB
        summaries_docs = mongo_manager.get_all_summaries(limit=limit, skip=offset)
        total_count = mongo_manager.count_summaries()
        
        # Convert to expected format
        summaries = []
        for doc in summaries_docs:
            summary = {
                'url': doc.get('url'),
                'title': doc.get('title'),
                'summary': doc.get('summary'),
                'key_points': doc.get('key_points', ''),
                'sentiment': doc.get('sentiment'),
                'word_count': doc.get('word_count'),
                'processing_time': doc.get('processing_time'),
                'created_at': doc.get('created_at'),
                'updated_at': doc.get('updated_at')
            }
            summaries.append(summary)
        
        # Apply search filter if provided
        if search:
            search_lower = search.lower()
            filtered_summaries = []
            for summary in summaries:
                if (search_lower in summary.get('title', '').lower() or
                    search_lower in summary.get('summary', '').lower() or
                    search_lower in summary.get('url', '').lower()):
                    filtered_summaries.append(summary)
            summaries = filtered_summaries
            # Note: This is a simple client-side filter. For production, consider MongoDB text search
        
        return {
            'summaries': summaries,
            'total_count': total_count,
            'total_pages': (total_count + limit - 1) // limit,
            'current_page': page
        }
    except Exception as e:
        logger.error(f"Error getting summaries from MongoDB: {e}")
        return {
            'summaries': [],
            'total_count': 0,
            'total_pages': 0,
            'current_page': page
        }

def get_status_data():
    """Get status data from MongoDB and LLM processor"""
    try:
        # Get total summaries count from MongoDB
        mongo_manager = get_mongo_manager()
        stats = mongo_manager.get_database_stats()
        total_summaries = stats.get('summaries_count', 0)
        
        # Get processing status from LLM processor
        try:
            response = requests.get(f"{LLM_PROCESSOR_URL}/api/status", timeout=5)
            if response.status_code == 200:
                llm_data = response.json()
                # Map LLM processor fields to expected fields
                processing_in_progress = llm_data.get('data', {}).get('processing_in_progress', False)
                processing_status = 'Processing' if processing_in_progress else 'Idle'
                llm_model = llm_data.get('data', {}).get('local_llm_model', 'Unknown')
            else:
                processing_status = 'Error'
                llm_model = 'Unknown'
        except Exception as e:
            logger.error(f"Error connecting to LLM processor: {e}")
            processing_status = 'Offline'
            llm_model = 'Unknown'
        
        return {
            'total_summaries': total_summaries,
            'processing_status': processing_status,
            'llm_model': llm_model
        }
    except Exception as e:
        logger.error(f"Error getting status data: {e}")
        return {
            'total_summaries': 0,
            'processing_status': 'Error',
            'llm_model': 'Unknown'
        }

@app.route("/")
def index():
    """Main page - optimized for memory efficiency"""
    return render_template('summary_index.html')

@app.route("/api/status")
def get_status():
    """Get system status - optimized for memory efficiency"""
    try:
        status_data = get_status_data()
        return jsonify({
            'success': True,
            'data': status_data
        })
    except Exception as e:
        logger.error(f"Error getting status: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route("/api/summaries")
def get_summaries():
    """Get summaries with pagination and search - optimized for memory efficiency"""
    try:
        page = int(request.args.get('page', 1))
        limit = int(request.args.get('limit', 12))
        search = request.args.get('search', '').strip()
        
        # Validate parameters
        if page < 1:
            page = 1
        if limit < 1 or limit > 100:
            limit = 12
        
        result = get_summaries_with_pagination(page, limit, search)
        
        return jsonify({
            'success': True,
            'data': result
        })
    except Exception as e:
        logger.error(f"Error getting summaries: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route("/api/process-all", methods=["POST"])
def process_all():
    """Process all unprocessed content - optimized for memory efficiency"""
    try:
        response = requests.post(f"{LLM_PROCESSOR_URL}/api/process-all", timeout=10)
        if response.status_code == 200:
            return jsonify(response.json())
        else:
            return jsonify({
                'success': False,
                'error': f'LLM processor returned status {response.status_code}'
            }), 500
    except Exception as e:
        logger.error(f"Error processing all content: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route("/api/health")
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'service': 'summary-display-server',
        'llm_processor_url': LLM_PROCESSOR_URL
    })

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5004, debug=False) 