"""
Configuration settings for AR_VR Helper RAG application
"""
import os
from pathlib import Path

# Project paths
PROJECT_ROOT = Path(__file__).parent.parent
DATA_DIR = PROJECT_ROOT / "data"
DOCS_SOURCE_DIR = Path(r"C:\Users\Maram Deepak\Desktop\hackathon\AR_VR")
VECTOR_DB_PATH = DATA_DIR / "chroma_db"

# API Configuration
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
GEMINI_MODEL = "gemini-1.5-pro"

# Targetprocess API Configuration
TARGETPROCESS_DOMAIN = os.getenv("TARGETPROCESS_DOMAIN", "")
TARGETPROCESS_TOKEN = os.getenv("TARGETPROCESS_TOKEN", "")

# Embedding Configuration
EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"
CHUNK_SIZE = 1000
CHUNK_OVERLAP = 200

# Vector Database Configuration
COLLECTION_NAME = "automation_rules_docs"
SIMILARITY_THRESHOLD = 0.7
MAX_RESULTS = 5

# Streamlit Configuration
APP_TITLE = "AR/VR Automation Rules Helper"
APP_DESCRIPTION = "AI Assistant for creating automation and validation rules"

# Create directories if they don't exist
DATA_DIR.mkdir(exist_ok=True)
VECTOR_DB_PATH.mkdir(exist_ok=True)