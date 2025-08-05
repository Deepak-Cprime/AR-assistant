"""
Streamlit web interface for AR_VR Helper RAG system
"""
import streamlit as st
import sys
import os
from pathlib import Path
from dotenv import load_dotenv
import json
import time

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from src.rag_system import RAGSystem
from config.config import *

# Page configuration
st.set_page_config(
    page_title="AR/VR Automation Rules Helper",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

@st.cache_resource
def load_rag_system():
    """Load and cache the RAG system"""
    # Load environment variables
    env_file = Path(__file__).parent.parent / ".env"
    if env_file.exists():
        load_dotenv(env_file)
    
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        st.error("OPENAI_API_KEY not found in environment variables")
        st.stop()
    
    # Check for TargetProcess credentials (try both naming conventions)
    tp_domain = os.getenv("TP_DOMAIN", "") or os.getenv("TARGETPROCESS_DOMAIN", "")
    tp_token = os.getenv("TP_TOKEN", "") or os.getenv("TARGETPROCESS_TOKEN", "")
    
    if tp_domain and tp_token:
        st.info(f"🔗 TargetProcess integration enabled for domain: {tp_domain}")
    else:
        st.warning("⚠️ TargetProcess integration disabled - TP_DOMAIN/TARGETPROCESS_DOMAIN and TP_TOKEN/TARGETPROCESS_TOKEN not configured")
    
    try:
        rag = RAGSystem(
            docs_source_dir=str(DOCS_SOURCE_DIR),
            vector_db_path=str(VECTOR_DB_PATH),
            collection_name=COLLECTION_NAME,
            openai_api_key=api_key,
            tp_domain=tp_domain,
            tp_token=tp_token,
            embedding_model=EMBEDDING_MODEL,
            chunk_size=CHUNK_SIZE,
            chunk_overlap=CHUNK_OVERLAP
        )
        
        # Initialize database
        with st.spinner("Initializing knowledge base..."):
            rag.initialize_database()
        
        return rag
    
    except Exception as e:
        st.error(f"Failed to initialize system: {e}")
        st.stop()

def display_system_stats(rag):
    """Display system statistics in sidebar"""
    stats = rag.get_system_stats()
    
    st.sidebar.header("📊 System Status")
    
    if stats.get('database_stats'):
        st.sidebar.metric(
            "Documents in KB", 
            stats['database_stats'].get('total_documents', 0)
        )
    
    st.sidebar.metric(
        "OpenAI API", 
        "✅ Connected" if stats.get('openai_connected') else "❌ Error"
    )
    
    # TargetProcess integration status
    tp_status = "✅ Connected" if rag.metadata_fetcher else "⚠️ Not configured"
    st.sidebar.metric("TargetProcess", tp_status)
    
    if st.sidebar.button("🔄 Refresh Stats"):
        st.cache_resource.clear()
        st.rerun()

def main():
    """Main Streamlit app"""
    st.title("🤖 AR/VR Automation Rules Helper")
    st.markdown("*AI Assistant for creating and managing Targetprocess automation rules*")
    
    # Load RAG system
    rag = load_rag_system()
    
    # Sidebar
    display_system_stats(rag)
    
    st.sidebar.header("🎯 Query Options")
    
    # Query type selection
    query_type = st.sidebar.selectbox(
        "Select Query Type",
        ["general", "create_automation", "explain_rule", "improve_rule"],
        format_func=lambda x: {
            "general": "💬 General Question",
            "create_automation": "⚡ Create Automation Rule", 
            "explain_rule": "📖 Explain Existing Rule",
            "improve_rule": "🔧 Improve Rule"
        }[x]
    )
    
    # Document type filter
    doc_types = rag.get_available_doc_types()
    doc_type_filter = st.sidebar.selectbox(
        "Filter by Document Type (Optional)",
        ["None"] + doc_types,
        help="Filter results to specific documentation types"
    )
    
    if doc_type_filter == "None":
        doc_type_filter = None
    
    # Advanced options
    with st.sidebar.expander("🔧 Advanced Options"):
        max_results = st.slider("Max Results", 1, 10, 3)
        similarity_threshold = st.slider("Similarity Threshold", 0.1, 1.0, 0.7, 0.1)
    
    # Main interface
    st.header("💭 Ask Your Question")
    
    # Query input
    if query_type == "create_automation":
        user_query = st.text_area(
            "Describe the automation rule you want to create:",
            placeholder="Example: Create a rule that automatically assigns bugs to the current release when they are created in the 'Mobile App' project",
            height=100
        )
    elif query_type == "explain_rule":
        user_query = st.text_area(
            "Paste the rule you want explained:",
            placeholder="Paste your JSON automation rule or validation rule here...",
            height=150
        )
    elif query_type == "improve_rule":
        user_query = st.text_area(
            "Paste the rule you want to improve:",
            placeholder="Paste your existing rule here for improvement suggestions...",
            height=150
        )
    else:
        user_query = st.text_area(
            "Ask any question about automation rules:",
            placeholder="Example: How do I create a validation rule that prevents editing closed tasks?",
            height=100
        )
    
    # Example queries
    with st.expander("💡 Example Queries"):
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("**Automation Rules:**")
            st.markdown("- Create a rule that assigns team members when a user story is created")
            st.markdown("- How do I automatically move items to 'In Progress' when work starts?")
            st.markdown("- Create a rule that sends Slack notifications for overdue tasks")
            
        with col2:
            st.markdown("**Validation Rules:**") 
            st.markdown("- Prevent editing tasks in final state")
            st.markdown("- Require time tracking before closing user stories")
            st.markdown("- Only allow project managers to change budgets")
    
    # Process query
    if st.button("🚀 Get Answer", type="primary", use_container_width=True):
        if not user_query.strip():
            st.warning("Please enter a question or rule to analyze.")
            return
        
        with st.spinner("🔍 Searching knowledge base and generating response..."):
            result = rag.query(
                user_query,
                query_type=query_type,
                doc_type_filter=doc_type_filter,
                max_results=max_results,
                similarity_threshold=similarity_threshold
            )
        
        # Display results
        if result['success']:
            st.success("✅ Response generated successfully!")
            
            # Main response
            st.header("📋 Response")
            st.markdown(result['response'])
            
            # Context information
            if result['context_docs']:
                with st.expander(f"📚 Source Documents ({len(result['context_docs'])} found)"):
                    for i, doc in enumerate(result['context_docs'], 1):
                        metadata = doc.get('metadata', {})
                        
                        st.markdown(f"**Document {i}: {metadata.get('title', 'Unknown')}**")
                        st.markdown(f"*File: {metadata.get('file_name', 'Unknown')}*")
                        st.markdown(f"*Type: {metadata.get('doc_type', 'general')}*")
                        
                        if 'distance' in doc:
                            similarity = 1 - doc['distance']
                            st.markdown(f"*Similarity: {similarity:.2%}*")
                        
                        with st.expander(f"View content from document {i}"):
                            st.text(doc.get('content', '')[:500] + "..." if len(doc.get('content', '')) > 500 else doc.get('content', ''))
                        
                        st.markdown("---")
            
            # Metadata
            with st.expander("🔍 Query Metadata"):
                st.json(result['metadata'])
        
        else:
            st.error(f"❌ Error: {result.get('error', 'Unknown error')}")
            
            if result.get('context_docs'):
                st.info("Some context was found, but response generation failed.")
    
    # Footer
    st.markdown("---")
    st.markdown("*Built with Streamlit, ChromaDB, Sentence Transformers, and OpenAI*")

if __name__ == "__main__":
    main()
    