# Backend Services - RAG System Implementation

This directory contains the core backend services implementing a sophisticated RAG (Retrieval-Augmented Generation) system for TargetProcess automation rule generation.

## Technical Architecture & Methods

### 1. RAG System Core (`rag_system.py`)

**Advanced RAG Implementation**
- **Multi-phase Retrieval**: Implements priority-based document retrieval with weighted scoring
- **Entity-aware Processing**: Automatic entity type detection from user queries using regex patterns
- **Context Enrichment**: Combines vector similarity search with TargetProcess metadata
- **Query Optimization**: Dynamic query expansion and refinement based on search results

**Key Techniques:**
- **Semantic Search with Re-ranking**: Uses sentence transformers for initial retrieval, then applies rule-specific re-ranking
- **Context Window Management**: Intelligent chunk selection to maximize relevant information within token limits
- **Fallback Strategies**: Multi-tier fallback system for robust operation when external APIs fail

### 2. Document Processing (`document_processor.py`)

**Advanced NLP Pipeline**
- **Markdown Processing**: BeautifulSoup + markdown parsing with metadata extraction
- **Semantic Chunking**: Overlapping text chunks with context preservation
- **Document Categorization**: Rule-based classification system for different document types
- **Embedding Generation**: Sentence-BERT embeddings optimized for technical documentation

**Vector Database Integration:**
- **ChromaDB**: Persistent vector storage with custom embedding functions
- **Similarity Search**: Cosine similarity with adjustable thresholds
- **Metadata Filtering**: Multi-dimensional filtering by document type, complexity, and entity
- **Performance Optimization**: Batch processing and efficient memory management

### 3. OpenAI Client (`openai_client.py`)

**AI Model Integration**
- **Multi-model Support**: Dynamic model selection with fallback hierarchy (GPT-4o → GPT-4 → GPT-3.5)
- **Complexity-aware Generation**: Adaptive prompting based on rule complexity levels
- **Context-aware Prompting**: Dynamic prompt engineering with TargetProcess-specific context
- **Response Formatting**: Structured output with code blocks, explanations, and usage examples

**Advanced Prompt Engineering:**
- **Template System**: Modular prompt templates for different rule types and complexity levels
- **Chain-of-thought**: Step-by-step reasoning for complex automation rules
- **Few-shot Learning**: Example-driven prompting using relevant documentation
- **Guardrails**: Built-in validation and error handling for generated code

### 4. Metadata Fetcher (`metadata_fetcher.py`)

**TargetProcess API Integration**
- **Dynamic Schema Discovery**: Runtime extraction of entity fields, states, and relationships
- **Intelligent Caching**: Multi-level caching with TTL for API response optimization
- **Field Validation**: Real-time field existence and access validation
- **Fallback Data**: Comprehensive default schemas when API access is unavailable

**API Techniques:**
- **Rate Limiting**: Built-in request throttling and retry mechanisms
- **Error Recovery**: Graceful degradation with informative error messages
- **Data Enrichment**: Combines API responses with inferred relationship patterns
- **Access Pattern Analysis**: Learns field usage patterns from sample data

## Advanced Implementation Patterns

### Asynchronous Processing
- **Non-blocking Operations**: Async/await patterns throughout for improved responsiveness
- **Concurrent Execution**: Parallel processing of multiple document chunks
- **Background Tasks**: Lazy loading and background database initialization

### Error Handling & Resilience
- **Circuit Breaker Pattern**: Prevents cascade failures when external APIs are down
- **Exponential Backoff**: Intelligent retry strategies with jitter
- **Graceful Degradation**: Maintains functionality with reduced features when services fail
- **Comprehensive Logging**: Structured logging with correlation IDs for debugging

### Performance Optimizations
- **Memory Management**: Efficient handling of large document collections
- **Batch Processing**: Vectorized operations for embedding generation
- **Connection Pooling**: Optimized database and API connections
- **Caching Strategies**: Multi-tier caching (in-memory, persistent, distributed)

### Security & Validation
- **Input Sanitization**: Comprehensive validation of user inputs and API responses
- **API Key Management**: Secure storage and rotation of sensitive credentials
- **Output Validation**: Generated code validation before returning to users
- **Access Control**: Role-based access to different complexity levels and features

## Integration Patterns

**Microservices Architecture**: Each module is designed as an independent service with clear interfaces
**Event-driven Communication**: Async messaging patterns for loose coupling
**Configuration Management**: Environment-based configuration with validation
**Health Monitoring**: Built-in health checks and metrics collection

## Code Examples

### RAG System Query Processing
```python
# src/rag_system.py - Advanced query processing with entity detection
class RAGSystem:
    def _detect_entity_type(self, query: str) -> str:
        """Detect TargetProcess entity type from user query"""
        entity_patterns = {
            'userstory': r'\b(?:user story|userstory|story|stories)\b',
            'bug': r'\b(?:bug|defect|issue|error)\b',
            'feature': r'\b(?:feature|epic|requirement)\b',
            'task': r'\b(?:task|subtask|work item)\b',
            'testcase': r'\b(?:test|testcase|testing|qa)\b'
        }
        
        query_lower = query.lower()
        for entity_type, pattern in entity_patterns.items():
            if re.search(pattern, query_lower):
                return entity_type
        return 'general'
    
    async def generate_response(self, query: str, context_docs: List[Dict]) -> str:
        """Generate AI response with context enrichment"""
        entity_type = self._detect_entity_type(query)
        
        # Multi-phase retrieval with weighted scoring
        relevant_chunks = self._rank_document_chunks(context_docs, query, entity_type)
        
        # Context window optimization
        optimized_context = self._optimize_context_window(relevant_chunks)
        
        return await self.openai_client.generate_rule_with_context(
            query=query,
            context=optimized_context,
            entity_type=entity_type
        )
```

### Vector Database Operations
```python
# src/document_processor.py - Advanced vector operations
class VectorDatabase:
    def similarity_search_with_metadata(self, query: str, entity_filter: str = None, 
                                      complexity_filter: str = None, n_results: int = 5):
        """Multi-dimensional similarity search with filtering"""
        
        # Generate query embedding
        query_embedding = self.embedding_model.encode([query])[0].tolist()
        
        # Build metadata filter
        where_conditions = {}
        if entity_filter:
            where_conditions["entity_type"] = entity_filter
        if complexity_filter:
            where_conditions["complexity"] = complexity_filter
            
        # Perform filtered vector search
        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=n_results,
            where=where_conditions,
            include=["documents", "metadatas", "distances"]
        )
        
        return self._process_search_results(results)
    
    def _calculate_weighted_relevance_score(self, base_similarity: float, 
                                          metadata: Dict) -> float:
        """Calculate weighted relevance based on metadata attributes"""
        weight_factors = {
            'complexity': {'beginner': 1.2, 'medium': 1.0, 'advanced': 0.8},
            'document_type': {'tutorial': 1.1, 'reference': 1.0, 'example': 1.3},
            'entity_match': 1.5  # Bonus for entity type match
        }
        
        weighted_score = base_similarity
        for factor, weights in weight_factors.items():
            if factor in metadata:
                weighted_score *= weights.get(metadata[factor], 1.0)
                
        return min(weighted_score, 1.0)  # Cap at 1.0
```

### AI Client Implementation
```python
# src/openai_client.py - Multi-model fallback system
class OpenAIClient:
    def _get_complexity_prompt_template(self, complexity: str) -> str:
        """Dynamic prompt templates based on complexity level"""
        templates = {
            "beginner": """
            Create a simple, well-documented automation rule for {entity_type}.
            Include:
            - Clear step-by-step explanation
            - Basic validation checks
            - Beginner-friendly comments
            - Error handling basics
            """,
            
            "medium": """
            Generate a production-ready automation rule for {entity_type}.
            Include:
            - Comprehensive validation
            - State transition logic
            - Proper error handling
            - Performance considerations
            """,
            
            "advanced": """
            Create an enterprise-level automation rule for {entity_type}.
            Include:
            - Complex business logic
            - Multi-entity relationships  
            - Advanced error recovery
            - Scalability patterns
            - Integration hooks
            """
        }
        return templates.get(complexity, templates["medium"])
    
    async def generate_rule_with_fallback(self, context: str, query: str, 
                                        complexity: str = "medium") -> str:
        """Generate rule with model fallback strategy"""
        fallback_models = ["gpt-4o", "gpt-4-turbo", "gpt-4", "gpt-3.5-turbo"]
        
        for model in fallback_models:
            try:
                response = await self._generate_with_model(
                    model=model,
                    context=context, 
                    query=query,
                    complexity=complexity
                )
                logger.info(f"Successfully generated response using {model}")
                return response
                
            except Exception as e:
                logger.warning(f"Model {model} failed: {e}, trying next...")
                continue
                
        raise Exception("All AI models failed to generate response")
```

### Chrome Extension Widget System
```javascript
// chrome_extension_simple/content.js - Dynamic widget architecture
class RuleGeneratorWidget {
    constructor() {
        this.isVisible = false;
        this.apiEndpoints = {
            'create_automation': '/api/generate-rule',
            'explain_rule': '/api/explain-rule', 
            'improve_rule': '/api/improve-rule',
            'general_query': '/api/query'
        };
        this.init();
    }
    
    async handleFormSubmit(formData) {
        const { ruleType, complexity, userInput } = formData;
        
        try {
            // Show loading state with specific message
            this.showLoadingState(this.getLoadingMessage(ruleType));
            
            // Dynamic endpoint selection
            const endpoint = this.apiEndpoints[ruleType];
            
            // API call with timeout and retry logic  
            const response = await this.makeApiCallWithRetry(endpoint, {
                query: userInput,
                complexity: complexity,
                context: this.extractPageContext()
            });
            
            // Format and display response
            this.displayResponse(response, ruleType);
            
        } catch (error) {
            this.handleError(error, ruleType);
        } finally {
            this.hideLoadingState();
        }
    }
    
    extractPageContext() {
        """Extract TargetProcess page context for better rule generation"""
        return {
            url: window.location.href,
            entityType: this.detectEntityFromPage(),
            pageTitle: document.title,
            activeProject: this.getActiveProject()
        };
    }
    
    async makeApiCallWithRetry(endpoint, data, maxRetries = 3) {
        for (let attempt = 1; attempt <= maxRetries; attempt++) {
            try {
                const response = await fetch(`http://localhost:8000${endpoint}`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(data),
                    timeout: 30000
                });
                
                if (!response.ok) throw new Error(`HTTP ${response.status}`);
                return await response.json();
                
            } catch (error) {
                if (attempt === maxRetries) throw error;
                
                // Exponential backoff
                await new Promise(resolve => 
                    setTimeout(resolve, Math.pow(2, attempt) * 1000)
                );
            }
        }
    }
}
```

This backend demonstrates advanced software engineering patterns including dependency injection, factory patterns, observer patterns, and clean architecture principles while maintaining high performance and reliability.