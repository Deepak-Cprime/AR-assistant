"""
FastAPI server for TargetProcess automation rules using full RAG system
Uses the same system as Streamlit app with Gemini AI, vector database, and TP integration
"""
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, Dict, Any, List
import logging
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Add parent directory to path to import from src
sys.path.append(str(Path(__file__).parent.parent))

# Import the full RAG system (same as Streamlit)
from src.rag_system import RAGSystem
from config.config import *

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
env_file = Path(__file__).parent.parent / ".env"
logger.info(f"Looking for .env file at: {env_file}")
if env_file.exists():
    logger.info(f"Loading .env file: {env_file}")
    load_dotenv(env_file)
    logger.info(f"TargetProcess domain from env: {os.getenv('TARGETPROCESS_DOMAIN')}")
    logger.info(f"TargetProcess token configured: {bool(os.getenv('TARGETPROCESS_TOKEN'))}")
else:
    logger.warning(f".env file not found at: {env_file}")

# Initialize FastAPI app
app = FastAPI(
    title="TargetProcess Rule Generator API (RAG-Powered)",
    description="Generate and explain automation rules using RAG system with Gemini AI",
    version="2.0.0"
)

# Enable CORS for Chrome extension
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize RAG system (same as Streamlit)
rag_system = None

def initialize_rag_system():
    """Initialize RAG system exactly like Streamlit app"""
    global rag_system
    
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        logger.error("GEMINI_API_KEY not found in environment variables")
        raise Exception("GEMINI_API_KEY not configured")
    
    # Get TargetProcess credentials
    tp_domain = os.getenv("TARGETPROCESS_DOMAIN")
    tp_token = os.getenv("TARGETPROCESS_TOKEN")
    
    logger.info(f"TargetProcess domain: {tp_domain}")
    logger.info(f"TargetProcess token configured: {bool(tp_token)}")
    
    try:
        rag_system = RAGSystem(
            docs_source_dir=str(DOCS_SOURCE_DIR),
            vector_db_path=str(VECTOR_DB_PATH),
            collection_name=COLLECTION_NAME,
            gemini_api_key=api_key,
            embedding_model=EMBEDDING_MODEL,
            chunk_size=CHUNK_SIZE,
            chunk_overlap=CHUNK_OVERLAP,
            tp_domain=tp_domain,
            tp_token=tp_token
        )
        
        # Initialize database
        logger.info("Initializing RAG system knowledge base...")
        rag_system.initialize_database()
        logger.info("RAG system initialized successfully")
        
        return rag_system
    
    except Exception as e:
        logger.error(f"Failed to initialize RAG system: {e}")
        raise

# Request/Response models
class RuleRequest(BaseModel):
    prompt: str
    rule_type: str = "create_automation"  # general, create_automation, explain_rule, improve_rule
    entity_type: Optional[str] = "UserStory"
    doc_type_filter: Optional[str] = None
    max_results: Optional[int] = 5  # Same as Streamlit default
    similarity_threshold: Optional[float] = 0.7  # Same as Streamlit default

class RuleResponse(BaseModel):
    success: bool
    response: str
    context_docs: List[Dict] = []
    metadata: Dict[str, Any] = {}
    error: Optional[str] = None

@app.on_event("startup")
async def startup_event():
    """Initialize RAG system on startup"""
    try:
        initialize_rag_system()
    except Exception as e:
        logger.error(f"Failed to start RAG system: {e}")
        # Don't fail startup, but log the error

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "TargetProcess Rule Generator API (RAG-Powered)",
        "version": "2.0.0",
        "endpoints": {
            "health": "/health",
            "generate_rule": "/generate-rule",
            "explain_rule": "/explain-rule", 
            "improve_rule": "/improve-rule",
            "general_query": "/general-query",
            "system_stats": "/system-stats"
        }
    }

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "TargetProcess Rule Generator (RAG-Powered)",
        "rag_system_initialized": rag_system is not None,
        "gemini_api_configured": bool(os.getenv("GEMINI_API_KEY"))
    }

@app.get("/system-stats")
async def get_system_stats():
    """Get system statistics"""
    if not rag_system:
        raise HTTPException(status_code=503, detail="RAG system not initialized")
    
    try:
        stats = rag_system.get_system_stats()
        return stats
    except Exception as e:
        logger.error(f"Error getting system stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/generate-rule", response_model=RuleResponse)
async def generate_rule(request: RuleRequest):
    """
    Generate automation rule using full RAG system (same as Streamlit)
    """
    if not rag_system:
        raise HTTPException(status_code=503, detail="RAG system not initialized. Please check GEMINI_API_KEY configuration.")
    
    try:
        logger.info(f"Generating rule: {request.prompt}")
        logger.info(f"Query params: type={request.rule_type}, max_results={request.max_results}, threshold={request.similarity_threshold}")
        
        # Use RAG system query method (same as Streamlit)
        result = rag_system.query(
            user_query=request.prompt,
            query_type=request.rule_type,
            doc_type_filter=request.doc_type_filter,
            max_results=request.max_results,
            similarity_threshold=request.similarity_threshold
        )
        
        logger.info(f"RAG system result: success={result.get('success')}, response_length={len(result.get('response', ''))}, context_docs={len(result.get('context_docs', []))}")
        
        if result['success']:
            logger.info("✅ Rule generation successful")
            return RuleResponse(
                success=True,
                response=result['response'],
                context_docs=result['context_docs'],
                metadata=result['metadata']
            )
        else:
            logger.error(f"❌ Rule generation failed: {result.get('error', 'Unknown error')}")
            return RuleResponse(
                success=False,
                response=result.get('response', 'Failed to generate rule'),
                error=result.get('error', 'Unknown error'),
                context_docs=result.get('context_docs', []),
                metadata=result.get('metadata', {})
            )
        
    except Exception as e:
        logger.error(f"💥 Exception in rule generation: {e}")
        logger.exception("Full exception traceback:")
        return RuleResponse(
            success=False,
            response=f"Error: {str(e)}",
            error=str(e)
        )

@app.post("/explain-rule", response_model=RuleResponse)
async def explain_rule(request: RuleRequest):
    """
    Explain existing automation rule using RAG system
    """
    if not rag_system:
        raise HTTPException(status_code=503, detail="RAG system not initialized")
    
    try:
        logger.info(f"Explaining rule: {request.prompt[:100]}...")
        
        # Use RAG system with explain_rule query type
        result = rag_system.query(
            user_query=request.prompt,
            query_type="explain_rule",
            doc_type_filter=request.doc_type_filter,
            max_results=request.max_results,
            similarity_threshold=request.similarity_threshold
        )
        
        if result['success']:
            return RuleResponse(
                success=True,
                response=result['response'],
                context_docs=result['context_docs'],
                metadata=result['metadata']
            )
        else:
            return RuleResponse(
                success=False,
                response=result.get('response', 'Failed to explain rule'),
                error=result.get('error', 'Unknown error'),
                context_docs=result.get('context_docs', []),
                metadata=result.get('metadata', {})
            )
        
    except Exception as e:
        logger.error(f"Error explaining rule: {e}")
        return RuleResponse(
            success=False,
            response=f"Error: {str(e)}",
            error=str(e)
        )

@app.post("/improve-rule", response_model=RuleResponse)
async def improve_rule(request: RuleRequest):
    """
    Improve existing automation rule using RAG system (same as Streamlit)
    """
    if not rag_system:
        raise HTTPException(status_code=503, detail="RAG system not initialized")
    
    try:
        logger.info(f"Improving rule: {request.prompt[:100]}...")
        
        # Use RAG system with improve_rule query type
        result = rag_system.query(
            user_query=request.prompt,
            query_type="improve_rule",
            doc_type_filter=request.doc_type_filter,
            max_results=request.max_results,
            similarity_threshold=request.similarity_threshold
        )
        
        logger.info(f"RAG system result: success={result.get('success')}, response_length={len(result.get('response', ''))}, context_docs={len(result.get('context_docs', []))}")
        
        if result['success']:
            logger.info("✅ Rule improvement successful")
            return RuleResponse(
                success=True,
                response=result['response'],
                context_docs=result['context_docs'],
                metadata=result['metadata']
            )
        else:
            logger.error(f"❌ Rule improvement failed: {result.get('error', 'Unknown error')}")
            return RuleResponse(
                success=False,
                response=result.get('response', 'Failed to improve rule'),
                error=result.get('error', 'Unknown error'),
                context_docs=result.get('context_docs', []),
                metadata=result.get('metadata', {})
            )
        
    except Exception as e:
        logger.error(f"💥 Exception in rule improvement: {e}")
        logger.exception("Full exception traceback:")
        return RuleResponse(
            success=False,
            response=f"Error: {str(e)}",
            error=str(e)
        )

@app.post("/general-query", response_model=RuleResponse)
async def general_query(request: RuleRequest):
    """
    Answer general questions using RAG system (same as Streamlit)
    """
    if not rag_system:
        raise HTTPException(status_code=503, detail="RAG system not initialized")
    
    try:
        logger.info(f"General query: {request.prompt[:100]}...")
        
        # Use RAG system with general query type
        result = rag_system.query(
            user_query=request.prompt,
            query_type="general",
            doc_type_filter=request.doc_type_filter,
            max_results=request.max_results,
            similarity_threshold=request.similarity_threshold
        )
        
        logger.info(f"RAG system result: success={result.get('success')}, response_length={len(result.get('response', ''))}, context_docs={len(result.get('context_docs', []))}")
        
        if result['success']:
            logger.info("✅ General query successful")
            return RuleResponse(
                success=True,
                response=result['response'],
                context_docs=result['context_docs'],
                metadata=result['metadata']
            )
        else:
            logger.error(f"❌ General query failed: {result.get('error', 'Unknown error')}")
            return RuleResponse(
                success=False,
                response=result.get('response', 'Failed to answer question'),
                error=result.get('error', 'Unknown error'),
                context_docs=result.get('context_docs', []),
                metadata=result.get('metadata', {})
            )
        
    except Exception as e:
        logger.error(f"💥 Exception in general query: {e}")
        logger.exception("Full exception traceback:")
        return RuleResponse(
            success=False,
            response=f"Error: {str(e)}",
            error=str(e)
        )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)