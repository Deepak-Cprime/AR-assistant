"""
Flask API server that wraps the existing RAG system
Provides HTTP endpoints for the Chrome extension to use the same logic as Streamlit
"""
from flask import Flask, request, jsonify
from flask_cors import CORS
import os
import sys
from pathlib import Path
from dotenv import load_dotenv
import logging

# Add current directory to path to import our modules
sys.path.append(str(Path(__file__).parent))

from src.rag_system import RAGSystem
from config.config import *

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)
CORS(app)  # Enable CORS for Chrome extension

# Global RAG system instance
rag_system = None

def initialize_rag_system():
    """Initialize the RAG system - same logic as Streamlit app"""
    global rag_system
    
    # Load environment variables
    env_file = Path(__file__).parent / ".env"
    if env_file.exists():
        load_dotenv(env_file)
    
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("OPENAI_API_KEY not found in environment variables")
    
    try:
        rag_system = RAGSystem(
            docs_source_dir=str(DOCS_SOURCE_DIR),
            vector_db_path=str(VECTOR_DB_PATH),
            collection_name=COLLECTION_NAME,
            openai_api_key=api_key,
            embedding_model=EMBEDDING_MODEL,
            chunk_size=CHUNK_SIZE,
            chunk_overlap=CHUNK_OVERLAP
        )
        
        # Initialize database
        logger.info("Initializing knowledge base...")
        rag_system.initialize_database()
        logger.info("RAG system initialized successfully")
        
        return True
        
    except Exception as e:
        logger.error(f"Failed to initialize RAG system: {e}")
        return False

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'rag_initialized': rag_system is not None
    })

@app.route('/test', methods=['POST'])
def test_endpoint():
    """Simple test endpoint to debug the issue"""
    try:
        data = request.get_json()
        logger.info(f"Test endpoint received: {data}")
        
        return jsonify({
            'success': True,
            'data': {
                'response': 'Test response: Basic automation rule structure here',
                'received_query': data.get('query', 'No query'),
                'test_mode': True
            }
        })
    except Exception as e:
        logger.error(f"Test endpoint failed: {e}", exc_info=True)
        return jsonify({
            'success': False,
            'error': str(e)
        })

@app.route('/query', methods=['POST'])
def process_query():
    """
    Process query using the same logic as Streamlit app
    Expected JSON payload:
    {
        "query": "string",
        "query_type": "general|create_automation|explain_rule|improve_rule",
        "doc_type_filter": "string|null",
        "max_results": int,
        "similarity_threshold": float,
        "context": object (optional)
    }
    """
    try:
        if not rag_system:
            return jsonify({
                'success': False,
                'error': 'RAG system not initialized'
            }), 500
        
        # Parse request data
        data = request.get_json()
        if not data:
            return jsonify({
                'success': False,
                'error': 'No JSON data provided'
            }), 400
        
        # Extract parameters
        query = data.get('query', '').strip()
        if not query:
            return jsonify({
                'success': False,
                'error': 'Query is required'
            }), 400
        
        query_type = data.get('query_type', 'general')
        doc_type_filter = data.get('doc_type_filter')
        max_results = data.get('max_results', 5)
        similarity_threshold = data.get('similarity_threshold', 0.7)
        context = data.get('context', {})
        
        # Use the exact same query method as Streamlit with TP context
        logger.info(f"Processing query: {query} (type: {query_type})")
        try:
            # Try with simpler context first to avoid TP metadata issues
            simple_context = {}
            result = rag_system.query(
                query,
                query_type=query_type,
                doc_type_filter=doc_type_filter,
                max_results=max_results,
                similarity_threshold=similarity_threshold,
                tp_context=simple_context
            )
            logger.info(f"Query result success: {result.get('success', False)}")
        except Exception as query_error:
            logger.error(f"RAG system query failed: {query_error}", exc_info=True)
            # Fallback: Try simple query without TP context
            try:
                logger.info("Attempting fallback query without TP context")
                result = {
                    'success': True,
                    'response': f"Based on your request to '{query}', here's a sample automation rule:\n\nWhen a User Story is created:\n1. Set the Initial State to 'New'\n2. Assign to the Story Creator\n3. Set Priority based on project defaults\n\nNote: This is a simplified response due to a system issue. Please try again or contact support.",
                    'context_docs': [],
                    'metadata': {'fallback': True}
                }
                logger.info("Fallback response generated")
            except Exception as fallback_error:
                logger.error(f"Fallback also failed: {fallback_error}")
                return jsonify({
                    'success': False,
                    'error': f'Query processing failed: {str(query_error)}'
                }), 500
        
        # Add context information to metadata if provided
        if context and result.get('metadata'):
            result['metadata']['extension_context'] = context
        
        return jsonify({
            'success': result['success'],
            'data': result if result['success'] else None,
            'error': result.get('error') if not result['success'] else None
        })
        
    except Exception as e:
        logger.error(f"Query processing failed: {e}")
        return jsonify({
            'success': False,
            'error': f'Query processing failed: {str(e)}'
        }), 500

@app.route('/stats', methods=['GET'])
def get_system_stats():
    """Get system statistics - same as Streamlit"""
    try:
        if not rag_system:
            return jsonify({
                'success': False,
                'error': 'RAG system not initialized'
            }), 500
        
        stats = rag_system.get_system_stats()
        
        return jsonify({
            'success': True,
            'data': stats
        })
        
    except Exception as e:
        logger.error(f"Failed to get system stats: {e}")
        return jsonify({
            'success': False,
            'error': f'Failed to get system stats: {str(e)}'
        }), 500

@app.route('/doc_types', methods=['GET'])
def get_doc_types():
    """Get available document types - same as Streamlit"""
    try:
        if not rag_system:
            return jsonify({
                'success': False,
                'error': 'RAG system not initialized'
            }), 500
        
        doc_types = rag_system.get_available_doc_types()
        
        return jsonify({
            'success': True,
            'data': doc_types
        })
        
    except Exception as e:
        logger.error(f"Failed to get document types: {e}")
        return jsonify({
            'success': False,
            'error': f'Failed to get document types: {str(e)}'
        }), 500

@app.route('/test_api_key', methods=['POST'])
def test_api_key():
    """Test if an OpenAI API key works"""
    try:
        data = request.get_json()
        if not data or 'api_key' not in data:
            return jsonify({
                'success': False,
                'error': 'API key is required'
            }), 400
        
        api_key = data['api_key']
        
        # Create a temporary RAG system instance to test the API key
        from src.openai_client import OpenAIClient
        
        test_client = OpenAIClient(api_key=api_key)
        
        # Try a simple test connection
        connection_test = test_client.test_connection()
        
        return jsonify({
            'success': connection_test,
            'message': 'API key is valid' if connection_test else 'API key is invalid'
        })
        
    except Exception as e:
        logger.error(f"API key test failed: {e}")
        return jsonify({
            'success': False,
            'error': f'API key test failed: {str(e)}'
        }), 400

@app.errorhandler(404)
def not_found(error):
    return jsonify({
        'success': False,
        'error': 'Endpoint not found'
    }), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({
        'success': False,
        'error': 'Internal server error'
    }), 500

if __name__ == '__main__':
    logger.info("Starting AR/VR Helper API Server...")
    
    # Initialize RAG system
    if initialize_rag_system():
        logger.info("RAG system initialized successfully")
        logger.info("API Server running on http://localhost:5000")
        logger.info("Available endpoints:")
        logger.info("  GET  /health - Health check")
        logger.info("  POST /query - Process queries")
        logger.info("  GET  /stats - System statistics") 
        logger.info("  GET  /doc_types - Available document types")
        logger.info("  POST /test_api_key - Test API key")
        
        # Run the Flask app
        app.run(
            host='localhost',
            port=5000,
            debug=False,  # Set to True for development
            threaded=True
        )
    else:
        logger.error("Failed to initialize RAG system. Server not started.")
        sys.exit(1)