"""
Main application entry point for AR_VR Helper
Command-line interface for the RAG system
"""
import os
import sys
from pathlib import Path
import argparse
from dotenv import load_dotenv

# Add src to path
sys.path.append(str(Path(__file__).parent / "src"))

from src.rag_system import RAGSystem
from config.config import *

def load_environment():
    """Load environment variables"""
    env_file = Path(__file__).parent / ".env"
    if env_file.exists():
        load_dotenv(env_file)
    
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        print("Error: GEMINI_API_KEY not found in environment variables")
        print("Please set your Gemini API key in .env file or environment")
        sys.exit(1)
    
    return api_key

def initialize_rag_system(api_key: str, force_rebuild: bool = False) -> RAGSystem:
    """Initialize the RAG system"""
    print("Initializing AR_VR Helper RAG System...")
    
    rag = RAGSystem(
        docs_source_dir=str(DOCS_SOURCE_DIR),
        vector_db_path=str(VECTOR_DB_PATH),
        collection_name=COLLECTION_NAME,
        gemini_api_key=api_key,
        tp_domain=os.getenv("TARGETPROCESS_DOMAIN", ""),
        tp_token=os.getenv("TARGETPROCESS_TOKEN", ""),
        embedding_model=EMBEDDING_MODEL,
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP
    )
    
    # Validate setup
    print("Validating system setup...")
    is_valid, issues = rag.validate_setup()
    
    if not is_valid:
        print("Setup validation failed:")
        for issue in issues:
            print(f"  - {issue}")
        sys.exit(1)
    
    # Initialize database
    print("Initializing vector database...")
    if not rag.initialize_database(force_rebuild=force_rebuild):
        print("Failed to initialize database")
        sys.exit(1)
    
    return rag

def interactive_mode(rag: RAGSystem):
    """Run interactive query mode"""
    print("\n" + "="*60)
    print("AR_VR Helper - Interactive Mode")
    print("="*60)
    print("Commands:")
    print("  help - Show this help")
    print("  stats - Show system statistics")
    print("  types - Show available document types")
    print("  exit - Exit the program")
    print("  Or just type your question about automation rules")
    print("-"*60)
    
    while True:
        try:
            user_input = input("\n🤖 Ask me about automation rules: ").strip()
            
            if not user_input:
                continue
                
            if user_input.lower() in ['exit', 'quit', 'q']:
                print("Goodbye!")
                break
                
            elif user_input.lower() == 'help':
                print("""
Available query types:
1. General questions about automation rules
2. Create automation rule: "Create a rule that..."
3. Explain existing rule: "Explain this rule: [paste rule here]"
4. Improve rule: "How can I improve this rule: [paste rule here]"

Example queries:
- "How do I create an automation rule that assigns bugs to the current release?"
- "Create a validation rule that prevents editing closed tasks"
- "What are the different trigger types for automation rules?"
- "Show me examples of JavaScript actions in automation rules"
""")
                continue
                
            elif user_input.lower() == 'stats':
                stats = rag.get_system_stats()
                print(f"\nSystem Statistics:")
                print(f"  Database documents: {stats.get('database_stats', {}).get('total_documents', 'Unknown')}")
                print(f"  Gemini connected: {stats.get('gemini_connected', False)}")
                print(f"  Initialized: {stats.get('is_initialized', False)}")
                continue
                
            elif user_input.lower() == 'types':
                doc_types = rag.get_available_doc_types()
                print(f"\nAvailable document types:")
                for doc_type in doc_types:
                    print(f"  - {doc_type}")
                continue
            
            # Determine query type
            query_type = "general"
            if user_input.lower().startswith("create"):
                query_type = "create_automation"
            elif "explain" in user_input.lower():
                query_type = "explain_rule"
            elif "improve" in user_input.lower() or "better" in user_input.lower():
                query_type = "improve_rule"
            
            print("🔍 Searching documentation...")
            result = rag.query(user_input, query_type=query_type)
            
            if result['success']:
                print("\n📋 Response:")
                print("-" * 40)
                print(result['response'])
                
                if result['context_docs']:
                    print(f"\n📚 Based on {len(result['context_docs'])} relevant documents")
            else:
                print(f"\n❌ Error: {result.get('error', 'Unknown error')}")
                
        except KeyboardInterrupt:
            print("\n\nGoodbye!")
            break
        except Exception as e:
            print(f"Error: {e}")

def single_query_mode(rag: RAGSystem, query: str, query_type: str):
    """Process single query and exit"""
    print(f"Processing query: {query}")
    
    result = rag.query(query, query_type=query_type)
    
    if result['success']:
        print("\nResponse:")
        print("="*60)
        print(result['response'])
        print("="*60)
        
        if result['context_docs']:
            print(f"\nBased on {len(result['context_docs'])} relevant documents")
    else:
        print(f"Error: {result.get('error', 'Unknown error')}")
        sys.exit(1)

def main():
    """Main function"""
    parser = argparse.ArgumentParser(description="AR_VR Helper - Automation Rules Assistant")
    parser.add_argument("--query", "-q", help="Single query to process")
    parser.add_argument("--type", "-t", choices=["general", "create_automation", "explain_rule", "improve_rule"], 
                       default="general", help="Type of query")
    parser.add_argument("--rebuild", "-r", action="store_true", help="Force rebuild vector database")
    parser.add_argument("--stats", "-s", action="store_true", help="Show system statistics")
    
    args = parser.parse_args()
    
    # Load environment
    api_key = load_environment()
    
    # Initialize system
    rag = initialize_rag_system(api_key, force_rebuild=args.rebuild)
    
    if args.stats:
        stats = rag.get_system_stats()
        print("\nSystem Statistics:")
        print(f"  Database documents: {stats.get('database_stats', {}).get('total_documents', 'Unknown')}")
        print(f"  Gemini connected: {stats.get('gemini_connected', False)}")
        print(f"  Initialized: {stats.get('is_initialized', False)}")
        print(f"  Available doc types: {len(stats.get('available_doc_types', []))}")
        return
    
    if args.query:
        single_query_mode(rag, args.query, args.type)
    else:
        interactive_mode(rag)

if __name__ == "__main__":
    main()