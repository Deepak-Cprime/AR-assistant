"""
Document processing module for RAG system
Handles markdown file parsing, chunking, and embedding
"""
import os
import re
from pathlib import Path
from typing import List, Dict, Any
import markdown
from bs4 import BeautifulSoup
from sentence_transformers import SentenceTransformer
import chromadb
from chromadb.utils import embedding_functions
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DocumentProcessor:
    def __init__(self, embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2", 
                 chunk_size: int = 1000, chunk_overlap: int = 200):
        """
        Initialize document processor with embedding model and chunking parameters
        """
        self.embedding_model = SentenceTransformer(embedding_model)
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        
    def extract_text_from_markdown(self, file_path: Path) -> Dict[str, Any]:
        """
        Extract clean text from markdown file
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Convert markdown to HTML
            html = markdown.markdown(content, extensions=['tables', 'fenced_code'])
            
            # Parse HTML and extract text
            soup = BeautifulSoup(html, 'html.parser')
            
            # Extract title (first h1 or filename)
            title_elem = soup.find('h1')
            title = title_elem.get_text().strip() if title_elem else file_path.stem
            
            # Extract all text content
            text_content = soup.get_text()
            
            # Clean up text
            text_content = re.sub(r'\n\s*\n', '\n\n', text_content)
            text_content = text_content.strip()
            
            return {
                'title': title,
                'content': text_content,
                'file_path': str(file_path),
                'file_name': file_path.name
            }
            
        except Exception as e:
            logger.error(f"Error processing {file_path}: {e}")
            return None
    
    def chunk_text(self, text: str, metadata: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Split text into overlapping chunks for better retrieval
        """
        words = text.split()
        chunks = []
        
        for i in range(0, len(words), self.chunk_size - self.chunk_overlap):
            chunk_words = words[i:i + self.chunk_size]
            chunk_text = ' '.join(chunk_words)
            
            chunk_metadata = metadata.copy()
            chunk_metadata.update({
                'chunk_id': len(chunks),
                'chunk_start': i,
                'chunk_end': min(i + self.chunk_size, len(words))
            })
            
            chunks.append({
                'text': chunk_text,
                'metadata': chunk_metadata
            })
            
        return chunks
    
    def process_markdown_files(self, docs_dir: Path) -> List[Dict[str, Any]]:
        """
        Process all markdown files in directory and return chunks
        """
        all_chunks = []
        markdown_files = list(docs_dir.glob("*.md"))
        
        logger.info(f"Found {len(markdown_files)} markdown files")
        
        for file_path in markdown_files:
            logger.info(f"Processing: {file_path.name}")
            
            doc_data = self.extract_text_from_markdown(file_path)
            if doc_data:
                # Determine document type based on filename
                doc_type = self._categorize_document(file_path.name)
                doc_data['doc_type'] = doc_type
                
                # Create chunks
                chunks = self.chunk_text(doc_data['content'], {
                    'title': doc_data['title'],
                    'file_path': doc_data['file_path'],
                    'file_name': doc_data['file_name'],
                    'doc_type': doc_type
                })
                
                all_chunks.extend(chunks)
        
        logger.info(f"Created {len(all_chunks)} text chunks")
        return all_chunks
    
    def _categorize_document(self, filename: str) -> str:
        """
        Categorize document based on filename patterns with priority levels
        """
        filename_lower = filename.lower()
        
        # High priority: Working examples with complete implementations
        if 'automation rules' in filename_lower and 'examples' in filename_lower and 'actions in targetprocess' in filename_lower:
            return 'working_examples_high_priority'
        
        # High priority: JavaScript API reference with exact syntax
        elif 'javascript' in filename_lower and 'reference' in filename_lower:
            return 'javascript_api_reference'
            
        # Medium priority: Specific automation examples
        elif 'automation rules' in filename_lower and 'examples' in filename_lower:
            if 'javascript' in filename_lower:
                return 'automation_javascript_examples'
            elif 'integration' in filename_lower:
                return 'automation_integration_examples'
            else:
                return 'automation_examples_medium'
        
        # Medium priority: Core automation documentation  
        elif 'automation rules' in filename_lower:
            if 'javascript' in filename_lower:
                return 'automation_javascript'
            elif 'setup' in filename_lower:
                return 'automation_setup'
            else:
                return 'automation_rules_core'
                
        # Lower priority categories
        elif 'validation rules' in filename_lower:
            if 'examples' in filename_lower:
                return 'validation_examples'
            else:
                return 'validation_rules'
        elif 'entity view' in filename_lower:
            return 'entity_customization'
        elif 'integration' in filename_lower:
            return 'integrations'
        elif 'devops' in filename_lower:
            return 'devops'
        else:
            return 'general'

class VectorDatabase:
    def __init__(self, db_path: str, collection_name: str):
        """
        Initialize ChromaDB vector database
        """
        self.client = chromadb.PersistentClient(path=db_path)
        self.collection_name = collection_name
        
        # Use sentence transformer embedding function
        self.embedding_function = embedding_functions.SentenceTransformerEmbeddingFunction(
            model_name="sentence-transformers/all-MiniLM-L6-v2"
        )
        
        # Get or create collection
        try:
            self.collection = self.client.get_collection(
                name=collection_name,
                embedding_function=self.embedding_function
            )
            logger.info(f"Loaded existing collection: {collection_name}")
        except:
            self.collection = self.client.create_collection(
                name=collection_name,
                embedding_function=self.embedding_function
            )
            logger.info(f"Created new collection: {collection_name}")
    
    def add_documents(self, chunks: List[Dict[str, Any]]):
        """
        Add document chunks to vector database
        """
        if not chunks:
            logger.warning("No chunks to add to database")
            return
            
        documents = []
        metadatas = []
        ids = []
        
        for i, chunk in enumerate(chunks):
            documents.append(chunk['text'])
            metadatas.append(chunk['metadata'])
            ids.append(f"chunk_{i}")
        
        # Add to collection in batches
        batch_size = 100
        for i in range(0, len(documents), batch_size):
            batch_docs = documents[i:i+batch_size]
            batch_metas = metadatas[i:i+batch_size]
            batch_ids = ids[i:i+batch_size]
            
            self.collection.add(
                documents=batch_docs,
                metadatas=batch_metas,
                ids=batch_ids
            )
            
        logger.info(f"Added {len(documents)} chunks to vector database")
    
    def search(self, query: str, n_results: int = 5, doc_type: str = None) -> List[Dict]:
        """
        Search for relevant documents
        """
        where_clause = None
        if doc_type:
            where_clause = {"doc_type": doc_type}
            
        results = self.collection.query(
            query_texts=[query],
            n_results=n_results,
            where=where_clause
        )
        
        # Format results
        formatted_results = []
        if results['documents']:
            for i, doc in enumerate(results['documents'][0]):
                formatted_results.append({
                    'content': doc,
                    'metadata': results['metadatas'][0][i],
                    'distance': results['distances'][0][i] if 'distances' in results else None
                })
        
        return formatted_results
    
    def get_collection_stats(self) -> Dict:
        """
        Get statistics about the collection
        """
        count = self.collection.count()
        return {
            'total_documents': count,
            'collection_name': self.collection_name
        }