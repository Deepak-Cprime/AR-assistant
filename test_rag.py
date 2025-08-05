"""
Quick test of the RAG system to see if it's finding documents
"""
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Add src to path
sys.path.append(str(Path(__file__).parent))

from src.rag_system import RAGSystem
from config.config import *

def test_rag():
    """Test the RAG system with different queries"""
    
    # Load environment variables
    env_file = Path(__file__).parent / ".env"
    if env_file.exists():
        load_dotenv(env_file)
    
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("ERROR: OPENAI_API_KEY not found")
        return False
    
    try:
        # Initialize RAG system
        print("Initializing RAG system...")
        rag_system = RAGSystem(
            docs_source_dir=str(DOCS_SOURCE_DIR),
            vector_db_path=str(VECTOR_DB_PATH),
            collection_name=COLLECTION_NAME,
            openai_api_key=api_key,
            embedding_model=EMBEDDING_MODEL,
            chunk_size=CHUNK_SIZE,
            chunk_overlap=CHUNK_OVERLAP
        )
        
        # Test queries
        test_queries = [
            "Create a bug when user story is blocked",
            "automation rule javascript",
            "create task",
            "blocked state",
            "automation"
        ]
        
        for query in test_queries:
            print(f"\n{'='*60}")
            print(f"Testing query: '{query}'")
            print('='*60)
            
            result = rag_system.query(
                query,
                query_type="create_automation", 
                max_results=3,
                similarity_threshold=0.3  # Very low threshold
            )
            
            if result.get('success'):
                context_docs = result.get('context_docs', [])
                print(f"SUCCESS: Found {len(context_docs)} documents")
                
                for i, doc in enumerate(context_docs):
                    print(f"\nDocument {i+1}:")
                    print(f"  Source: {doc.get('source', 'Unknown')}")
                    print(f"  Content preview: {doc.get('content', '')[:200]}...")
                    
            else:
                print(f"FAILED: {result.get('error', 'Unknown error')}")
                
        return True
        
    except Exception as e:
        print(f"Error testing RAG: {e}")
        return False

if __name__ == "__main__":
    print("Testing RAG System Document Retrieval")
    print("=" * 60)
    test_rag()