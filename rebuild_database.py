"""
Rebuild vector database with correct documents from AR_VR folder
"""
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Add src to path
sys.path.append(str(Path(__file__).parent))

from src.rag_system import RAGSystem
from config.config import *

def rebuild_database():
    """Rebuild the vector database with documents from AR_VR folder"""
    
    # Load environment variables
    env_file = Path(__file__).parent / ".env"
    if env_file.exists():
        load_dotenv(env_file)
    
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        print("ERROR: GEMINI_API_KEY not found in environment variables")
        return False
    
    print(f"Source Directory: {DOCS_SOURCE_DIR}")
    print(f"Vector DB Path: {VECTOR_DB_PATH}")
    
    # Check if source directory exists
    if not DOCS_SOURCE_DIR.exists():
        print(f"ERROR: Source directory does not exist: {DOCS_SOURCE_DIR}")
        return False
    
    # Count documents in source
    md_files = list(DOCS_SOURCE_DIR.glob("*.md"))
    print(f"Found {len(md_files)} markdown files to process")
    
    if len(md_files) == 0:
        print("ERROR: No markdown files found in source directory")
        return False
    
    try:
        # Initialize RAG system
        print("Initializing RAG system...")
        rag_system = RAGSystem(
            docs_source_dir=str(DOCS_SOURCE_DIR),
            vector_db_path=str(VECTOR_DB_PATH),
            collection_name=COLLECTION_NAME,
            gemini_api_key=api_key,
            embedding_model=EMBEDDING_MODEL,
            chunk_size=CHUNK_SIZE,
            chunk_overlap=CHUNK_OVERLAP
        )
        
        # Force rebuild the database
        print("Rebuilding vector database...")
        success = rag_system.initialize_database(force_rebuild=True)
        
        if success:
            print("Database rebuilt successfully!")
            
            # Test the database
            print("Testing database...")
            result = rag_system.query("create automation rule", max_results=3)
            
            if result.get('success') and result.get('context_docs'):
                print(f"Found {len(result['context_docs'])} relevant documents")
                print("Database is working correctly!")
                return True
            else:
                print("Database test failed - no documents found")
                return False
        else:
            print("Failed to rebuild database")
            return False
            
    except Exception as e:
        print(f"Error rebuilding database: {e}")
        return False

if __name__ == "__main__":
    print("Rebuilding Vector Database with AR_VR Documentation")
    print("=" * 60)
    
    success = rebuild_database()
    
    if success:
        print("\nDatabase rebuild completed successfully!")
        print("You can now run the Streamlit app with the updated database.")
    else:
        print("\nDatabase rebuild failed!")
        print("Please check the error messages above.")