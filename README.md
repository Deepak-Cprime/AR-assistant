# AR/VR Helper - TargetProcess Rule Generator

A comprehensive automation tool that helps generate validation and automation rules for TargetProcess using AI-powered document analysis. The system combines a Chrome extension, web interface, and intelligent RAG (Retrieval-Augmented Generation) backend to streamline rule creation processes.

## What This Application Does

This application assists users in generating TargetProcess automation and validation rules by:

- **Analyzing existing documentation** to understand rule patterns and requirements
- **Providing an intuitive Chrome extension** that works directly within TargetProcess pages
- **Offering a web interface** for detailed rule generation and management
- **Using AI to suggest relevant rules** based on context and historical data

## Unique Features & Techniques

### 🤖 **Advanced RAG Implementation**
- **Multi-phase Retrieval**: Priority-based document retrieval with weighted scoring algorithms
- **Entity-aware Processing**: Automatic detection of TargetProcess entity types (User Stories, Bugs, Features)
- **Context Enrichment**: Semantic search combined with metadata filtering for precise results
- **Fallback Strategies**: Multi-tier system ensuring robust operation even when APIs fail

### 🧠 **AI-Powered Rule Generation**
- **Multi-model Support**: Dynamic model selection (GPT-4o → GPT-4 → GPT-3.5) with intelligent fallbacks
- **Complexity-aware Prompting**: Adaptive AI responses based on rule complexity levels (Beginner → Expert)
- **Chain-of-thought Reasoning**: Step-by-step rule construction with detailed explanations
- **Few-shot Learning**: Example-driven prompting using relevant documentation patterns

### 🔧 **Chrome Extension Innovation**
- **Manifest V3 Architecture**: Modern service worker pattern with event-driven design
- **Dynamic DOM Injection**: Context-aware widget creation only on TargetProcess domains
- **Multi-mode Interface**: Create, Explain, Improve, and General query capabilities
- **Real-time Integration**: Seamless API communication with loading states and error recovery

### 📊 **Vector Database Intelligence**
- **ChromaDB Integration**: Persistent vector storage with custom embedding functions
- **Semantic Chunking**: Overlapping text processing with context preservation
- **Multi-dimensional Filtering**: Document categorization by type, complexity, and entity relationships
- **Performance Optimization**: Batch processing and efficient memory management

## Components Overview

### **Chrome Extension** ([`chrome_extension_simple/`](chrome_extension_simple/README.md))
Browser extension providing floating widget interface for TargetProcess integration
- **Key Technology**: Manifest V3, Content Scripts, Service Workers
- **Unique Features**: Dynamic DOM manipulation, real-time API integration, multi-mode operation
- **Implementation**: Class-based widget architecture with state management

### **Backend Services** ([`src/`](src/README.md))  
Core RAG system implementing advanced AI and document processing
- **Key Technology**: Python, ChromaDB, Sentence Transformers, OpenAI API
- **Unique Features**: Multi-phase retrieval, entity-aware processing, circuit breaker patterns
- **Implementation**: Microservices architecture with async processing and comprehensive error handling

### **API Integration**
- **Web Interface** (`streamlit_app/`): User-friendly dashboard for rule management
- **API Server** (`fastapi_server/`): RESTful API for component communication
- **Configuration** (`config/`): Environment-based configuration with validation

## Technical Architecture

```python
# Core RAG Pipeline Example
class RAGSystem:
    async def generate_rule(self, query: str, entity_type: str, complexity: str):
        # Multi-phase retrieval with weighted scoring
        relevant_docs = await self.retrieve_documents(query, entity_type)
        
        # Entity-aware context enrichment
        enriched_context = self.enrich_with_metadata(relevant_docs, entity_type)
        
        # Complexity-aware AI generation
        rule = await self.ai_client.generate_rule(
            context=enriched_context,
            complexity=complexity,
            entity_type=entity_type
        )
        
        return rule
```

## Advanced Implementation Patterns

- **Asynchronous Processing**: Non-blocking operations with concurrent document processing
- **Circuit Breaker Pattern**: Prevents cascade failures when external services are unavailable  
- **Event-driven Communication**: Loose coupling between components with async messaging
- **Graceful Degradation**: Maintains functionality with reduced features during service failures

## Getting Started

1. Install Python dependencies: `pip install -r requirements.txt`
2. Configure environment variables in `.env` file
3. Load the Chrome extension from `chrome_extension_simple/` directory
4. Run the Streamlit app: `python streamlit_app/run_app.py`
5. Start the API server: `python fastapi_server/main.py`

## Usage

1. Navigate to any TargetProcess page
2. Use the floating button to generate rules contextually
3. Access the web dashboard for detailed rule management
4. Leverage AI suggestions based on your documentation and requirements

For detailed technical information about each component, refer to the README files in the respective directories.