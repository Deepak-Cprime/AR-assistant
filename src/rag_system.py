"""
Complete RAG (Retrieval-Augmented Generation) system for automation rules
Combines document retrieval with Gemini AI generation
"""
import os
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
import logging
from datetime import datetime

from .document_processor import DocumentProcessor, VectorDatabase
from .gemini_client import GeminiClient
from .metadata_fetcher import TargetprocessMetadata

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class RAGSystem:
    def __init__(self, 
                 docs_source_dir: str,
                 vector_db_path: str,
                 collection_name: str,
                 gemini_api_key: str,
                 tp_domain: str = "",
                 tp_token: str = "",
                 embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2",
                 chunk_size: int = 1000,
                 chunk_overlap: int = 200):
        """
        Initialize complete RAG system
        """
        self.docs_source_dir = Path(docs_source_dir)
        self.vector_db_path = vector_db_path
        self.collection_name = collection_name
        
        # Initialize components
        self.doc_processor = DocumentProcessor(
            embedding_model=embedding_model,
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap
        )
        
        self.vector_db = VectorDatabase(
            db_path=vector_db_path,
            collection_name=collection_name
        )
        
        self.gemini_client = GeminiClient(
            api_key=gemini_api_key,
            model_name="gemini-1.5-flash"
        )
        
        # Initialize metadata fetcher if credentials provided
        self.metadata_fetcher = None
        if tp_domain and tp_token:
            try:
                self.metadata_fetcher = TargetprocessMetadata(tp_domain, tp_token)
                logger.info("Targetprocess metadata fetcher initialized")
            except Exception as e:
                logger.warning(f"Failed to initialize metadata fetcher: {e}")
        
        self.is_initialized = False
        
    def initialize_database(self, force_rebuild: bool = False) -> bool:
        """
        Initialize vector database with documents
        """
        try:
            # Check if database already has documents
            stats = self.vector_db.get_collection_stats()
            if stats['total_documents'] > 0 and not force_rebuild:
                logger.info(f"Database already initialized with {stats['total_documents']} documents")
                self.is_initialized = True
                return True
            
            if force_rebuild:
                logger.info("Force rebuilding database...")
                # Clear existing collection
                try:
                    self.vector_db.client.delete_collection(self.collection_name)
                    self.vector_db = VectorDatabase(
                        db_path=self.vector_db_path,
                        collection_name=self.collection_name
                    )
                except:
                    pass
            
            # Process documents
            logger.info(f"Processing documents from: {self.docs_source_dir}")
            chunks = self.doc_processor.process_markdown_files(self.docs_source_dir)
            
            if not chunks:
                logger.error("No document chunks created")
                return False
            
            # Add to vector database
            self.vector_db.add_documents(chunks)
            
            # Verify initialization
            stats = self.vector_db.get_collection_stats()
            logger.info(f"Database initialized with {stats['total_documents']} document chunks")
            
            self.is_initialized = True
            return True
            
        except Exception as e:
            logger.error(f"Error initializing database: {e}")
            return False
    
    def search_with_priority(self, user_query: str, max_results: int = 5) -> List[Dict]:
        """
        Search documents with priority for automation rule creation
        Uses adaptive query expansion and content-based ranking
        """
        # Since all documents have doc_type='general', don't filter by doc_type
        # Instead, use multiple query variations to get diverse results
        all_results = []
        seen_ids = set()
        
        # Create query variations for better semantic matching
        query_variations = [
            user_query,  # Original query
            f"{user_query} automation rule",
            f"{user_query} targetprocess",
            f"javascript {user_query}",
            user_query.replace("Create", "create").replace("create", "automation")
        ]
        
        # Search with multiple query variations (no doc_type filtering since all are 'general')
        for j, query in enumerate(query_variations):
            if len(all_results) >= max_results * 2:  # Get diverse results
                break
                
            results = self.vector_db.search(
                query=query.strip(),
                n_results=3  # Get more results per query
            )
            
            for i, result in enumerate(results):
                doc_id = result.get('id', f'result_{j}_{i}')  # Fallback ID for deduplication
                
                if doc_id not in seen_ids:
                    seen_ids.add(doc_id)
                    
                    # Assign priority scores
                    result['query_priority'] = j
                    
                    # Content-based scoring
                    content = result.get('content', '').lower()
                    metadata = result.get('metadata', {})
                    
                    # Calculate content relevance score
                    relevance_score = 0
                    
                    # Boost for working examples (contains code/JSON)
                    if any(pattern in content for pattern in ['command:', '```', 'script:', 'return {']):
                        relevance_score += 2
                        
                    # Boost for automation-specific content  
                    if any(pattern in content for pattern in ['targetprocess:', 'automation rule', 'javascript']):
                        relevance_score += 1
                        
                    # Boost for comprehensive examples
                    if len(content) > 1000 and 'example' in content:
                        relevance_score += 1
                        
                    # Boost for files with "comprehensive" in name
                    if 'comprehensive' in metadata.get('file_name', '').lower():
                        relevance_score += 1.5
                        
                    result['content_relevance'] = relevance_score
                    all_results.append(result)
        
        # Intelligent sorting: balance content relevance, query priority, and similarity
        all_results.sort(key=lambda x: (
            -x.get('content_relevance', 0),      # Content relevance (higher is better)
            x.get('query_priority', 999),        # Query priority (lower is better)
            x.get('distance', 1.0),             # Similarity score (lower is better)
            x.get('query_priority', 999)        # Query variation priority
        ))
        
        return all_results[:max_results]

    def query(self, 
              user_query: str, 
              query_type: str = "general",
              doc_type_filter: Optional[str] = None,
              max_results: int = 5,
              similarity_threshold: float = 0.7,
              tp_context: Dict = None) -> Dict[str, Any]:
        """
        Main query function that combines retrieval and generation with live TP data
        """
        if not self.is_initialized:
            logger.warning("Database not initialized. Attempting to initialize...")
            if not self.initialize_database():
                return {
                    'success': False,
                    'error': 'Failed to initialize database',
                    'response': 'Database initialization failed. Please check your configuration.',
                    'context_docs': [],
                    'metadata': {}
                }
        
        try:
            # Step 1: Retrieve relevant documents with priority for automation rules
            logger.info(f"Searching for documents related to: {user_query}")
            
            if query_type == "create_automation" and not doc_type_filter:
                # Use priority search for automation rule creation
                relevant_docs = self.search_with_priority(user_query, max_results)
                logger.info(f"Using priority search for automation rules")
            else:
                # Use standard search for other queries
                relevant_docs = self.vector_db.search(
                    query=user_query,
                    n_results=max_results,
                    doc_type=doc_type_filter
                )
            
            # Debug: Log similarity scores
            logger.info(f"Found {len(relevant_docs)} documents before filtering")
            for i, doc in enumerate(relevant_docs[:3]):
                distance = doc.get('distance', 1.0)
                similarity = 1.0 - distance
                logger.info(f"Doc {i+1}: distance={distance:.3f}, similarity={similarity:.3f}")
            
            # Filter by similarity threshold (more lenient)
            # Use a much more lenient threshold - ChromaDB distances can be high for semantic search
            max_distance = 1.2  # Allow distances up to 1.2 (very lenient for semantic search)
            filtered_docs = [
                doc for doc in relevant_docs 
                if doc.get('distance', 1.0) <= max_distance
            ]
            
            if not filtered_docs:
                logger.warning("No relevant documents found after filtering, using top results anyway")
                filtered_docs = relevant_docs[:3]  # Use top 3 regardless of threshold
            
            # Step 2: Get live TargetProcess metadata for precise automation rules
            entity_metadata = None
            live_tp_data = {}
            
            if query_type == "create_automation":
                # Extract entity type from query or tp_context
                entity_type = self._extract_entity_type(user_query, tp_context)
                logger.info(f"Extracted entity type: {entity_type}")
                
                if entity_type:
                    if self.metadata_fetcher:
                        try:
                            logger.info(f"Fetching live TargetProcess metadata for {entity_type}")
                            entity_metadata = self.metadata_fetcher.get_entity_metadata(entity_type)
                            
                            # Get additional context if provided (e.g., from Chrome extension)
                            if tp_context:
                                live_tp_data = self._enrich_with_tp_context(entity_metadata, tp_context)
                                
                            logger.info(f"Retrieved live metadata: {len(entity_metadata.get('standard_fields', []))} fields, {len(entity_metadata.get('states', []))} states")
                            
                        except Exception as e:
                            logger.warning(f"Failed to get live metadata for {entity_type}: {e}")
                            # Fall back to extracting entity info from context docs
                            entity_metadata = self._extract_entity_info_from_docs(filtered_docs, entity_type)
                    else:
                        logger.warning(f"Entity type '{entity_type}' detected but metadata_fetcher not available")
                elif self.metadata_fetcher:
                    logger.warning("Metadata fetcher available but no entity type detected from query")

            # Step 3: Generate response using both RAG context and live TP data
            if query_type == "create_automation":
                response = self.gemini_client.generate_automation_rule(
                    user_query, 
                    filtered_docs, 
                    entity_metadata,
                    live_tp_data
                )
            elif query_type == "explain_rule":
                response = self.gemini_client.explain_existing_rule(user_query, filtered_docs)
            elif query_type == "improve_rule":
                response = self.gemini_client.suggest_improvements(user_query, filtered_docs)
            else:  # general
                response = self.gemini_client.answer_question(user_query, filtered_docs)
            
            return {
                'success': True,
                'response': response,
                'context_docs': filtered_docs,
                'metadata': {
                    'query_type': query_type,
                    'num_context_docs': len(filtered_docs),
                    'doc_type_filter': doc_type_filter,
                    'entity_metadata': entity_metadata is not None,
                    'live_tp_data': bool(live_tp_data),
                    'timestamp': datetime.now().isoformat()
                }
            }
            
        except Exception as e:
            logger.error(f"Error processing query: {e}")
            return {
                'success': False,
                'error': str(e),
                'response': f'Error processing your request: {str(e)}',
                'context_docs': [],
                'metadata': {}
            }
    
    def _extract_entity_type(self, user_query: str, tp_context: Dict = None) -> Optional[str]:
        """
        Extract entity type from user query or TP context
        """
        # Check if provided in context (from Chrome extension)
        if tp_context and 'entityType' in tp_context:
            return tp_context['entityType']
        
        # Extract from query text
        query_lower = user_query.lower()
        
        # Common entity type patterns
        entity_patterns = {
            'user story': 'UserStory',
            'userstory': 'UserStory', 
            'story': 'UserStory',
            'bug': 'Bug',
            'task': 'Task',
            'feature': 'Feature',
            'epic': 'Epic',
            'portfolio epic': 'PortfolioEpic',
            'release': 'Release',
            'project': 'Project',
            'request': 'Request',
            'risk': 'Risk',
            'impediment': 'Impediment'
        }
        
        for pattern, entity_type in entity_patterns.items():
            if pattern in query_lower:
                return entity_type
        
        return None
    
    def _enrich_with_tp_context(self, entity_metadata: Dict, tp_context: Dict) -> Dict:
        """
        Enrich metadata with additional context from TargetProcess page
        """
        enriched_data = {
            'current_page_context': tp_context,
            'suggested_fields': [],
            'field_validations': {}
        }
        
        # Add field access patterns for JavaScript
        if 'standard_fields' in entity_metadata:
            for field in entity_metadata['standard_fields']:
                field_info = self.metadata_fetcher.validate_field_access(
                    entity_metadata['entity_type'], field
                )
                enriched_data['field_validations'][field] = field_info
        
        # Add suggestions based on current context
        if 'url' in tp_context:
            url = tp_context['url']
            if '/entity/' in url:
                enriched_data['context_type'] = 'entity_view'
            elif '/board/' in url:
                enriched_data['context_type'] = 'board_view'
            elif '/setup/' in url:
                enriched_data['context_type'] = 'setup_page'
        
        return enriched_data
    
    def _extract_entity_info_from_docs(self, docs: List[Dict], entity_type: str) -> Dict:
        """
        Extract entity information from retrieved documents as fallback
        """
        extracted_info = {
            'entity_type': entity_type,
            'source': 'documents',
            'standard_fields': [],
            'states': [],
            'relationships': []
        }
        
        # Scan document content for field names and patterns
        for doc in docs:
            content = doc.get('content', '').lower()
            
            # Look for common field patterns
            if 'args.current.' in content:
                # Extract field names from JavaScript patterns
                import re
                field_matches = re.findall(r'args\.current\.(\w+)', content, re.IGNORECASE)
                extracted_info['standard_fields'].extend(field_matches)
            
            # Look for state names
            if 'entitystate' in content or 'state' in content:
                state_matches = re.findall(r'"([A-Za-z\s]+)"', content)
                potential_states = [s for s in state_matches if len(s) < 20 and s.strip()]
                extracted_info['states'].extend(potential_states)
        
        # Remove duplicates and clean up
        extracted_info['standard_fields'] = list(set(extracted_info['standard_fields']))[:10]
        extracted_info['states'] = list(set(extracted_info['states']))[:10]
        
        return extracted_info

    def get_available_doc_types(self) -> List[str]:
        """
        Get list of available document types in the database
        """
        try:
            # This is a simplified approach - in a real implementation,
            # you might want to store this metadata separately
            return [
                'automation_rules',
                'automation_examples', 
                'automation_javascript',
                'automation_setup',
                'validation_rules',
                'entity_customization',
                'integrations',
                'devops',
                'general'
            ]
        except Exception as e:
            logger.error(f"Error getting doc types: {e}")
            return []
    
    def get_system_stats(self) -> Dict[str, Any]:
        """
        Get system statistics and health information
        """
        try:
            db_stats = self.vector_db.get_collection_stats()
            gemini_status = self.gemini_client.test_connection()
            
            return {
                'database_stats': db_stats,
                'gemini_connected': gemini_status,
                'is_initialized': self.is_initialized,
                'docs_source_dir': str(self.docs_source_dir),
                'available_doc_types': self.get_available_doc_types()
            }
        except Exception as e:
            logger.error(f"Error getting system stats: {e}")
            return {
                'error': str(e),
                'is_initialized': self.is_initialized
            }
    
    def search_documents_only(self, 
                             query: str, 
                             doc_type_filter: Optional[str] = None,
                             max_results: int = 10) -> List[Dict]:
        """
        Search documents without generating AI response
        """
        try:
            return self.vector_db.search(
                query=query,
                n_results=max_results,
                doc_type=doc_type_filter
            )
        except Exception as e:
            logger.error(f"Error searching documents: {e}")
            return []
    
    def validate_setup(self) -> Tuple[bool, List[str]]:
        """
        Validate that all components are properly configured
        """
        issues = []
        
        # Check if source documents exist
        if not self.docs_source_dir.exists():
            issues.append(f"Source documents directory not found: {self.docs_source_dir}")
        else:
            md_files = list(self.docs_source_dir.glob("*.md"))
            if not md_files:
                issues.append(f"No markdown files found in: {self.docs_source_dir}")
        
        # Check Gemini API
        try:
            if not self.gemini_client.test_connection():
                issues.append("Gemini API connection failed")
        except Exception as e:
            issues.append(f"Gemini API error: {str(e)}")
        
        # Check vector database
        try:
            self.vector_db.get_collection_stats()
        except Exception as e:
            issues.append(f"Vector database error: {str(e)}")
        
        return len(issues) == 0, issues
    
