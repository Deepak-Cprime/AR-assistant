# AR/VR Automation Rules Helper 🤖

An intelligent RAG (Retrieval-Augmented Generation) system that helps create, understand, and improve Targetprocess automation rules using AI. Built with ChromaDB for vector storage, Sentence Transformers for embeddings, and Google Gemini AI for natural language generation.

## ✨ Features

- **Smart Rule Generation**: Create automation rules from natural language descriptions
- **Rule Explanation**: Understand existing automation and validation rules 
- **Rule Improvement**: Get suggestions to optimize your existing rules
- **Document Search**: Find relevant documentation instantly
- **Multiple Interfaces**: Command-line and web-based Streamlit interface
- **Vector Database**: Fast semantic search through 150+ documentation files
- **AI-Powered**: Uses Google Gemini Pro for intelligent responses

## 🏗️ Architecture

```
AR_VR_helper/
├── src/                          # Core application code
│   ├── document_processor.py     # Markdown processing & embeddings
│   ├── gemini_client.py          # Google Gemini AI integration
│   ├── rag_system.py             # Main RAG orchestration
│   └── __init__.py
├── streamlit_app/               # Web interface
│   ├── app.py                   # Streamlit application
│   └── run_app.py               # App launcher
├── config/                      # Configuration files
│   └── config.py                # System settings
├── data/                        # Generated data (vector DB)
├── docs/                        # Documentation
├── main.py                      # CLI interface
├── requirements.txt             # Python dependencies
├── .env.example                 # Environment template
└── README.md                    # This file
```

## 🚀 Quick Start

### 1. Prerequisites

- Python 3.8+
- Google Gemini API key ([Get one here](https://makersuite.google.com/app/apikey))

### 2. Installation

```bash
# Clone or download the project
cd AR_VR_helper

# Install dependencies
pip install -r requirements.txt
```

### 3. Configuration

Create a `.env` file from the template:

```bash
cp .env.example .env
```

Edit `.env` and add your Gemini API key:

```env
GEMINI_API_KEY=your_gemini_api_key_here
```

### 4. Run the Application

#### Option A: Streamlit Web Interface (Recommended)

```bash
python streamlit_app/run_app.py
```

Then open http://localhost:8501 in your browser.

#### Option B: Command Line Interface

```bash
# Interactive mode
python main.py

# Single query
python main.py --query "Create a rule that assigns bugs to current release"

# Force rebuild database
python main.py --rebuild

# Show system stats
python main.py --stats
```

## 💡 Usage Examples

### Creating Automation Rules

**Query**: "Create a rule that automatically assigns new user stories to the team based on the project"

**Response**: Complete JSON configuration with source triggers, filters, and actions.

### Explaining Existing Rules

**Query**: "Explain this rule: [paste your JSON rule]"

**Response**: Detailed breakdown of what the rule does, when it triggers, and its effects.

### Validation Rules

**Query**: "Create a validation rule that prevents editing closed tasks"

**Response**: DSL expression and trigger configuration for the validation rule.

### Integration Examples

**Query**: "How do I send Slack notifications when a feature is completed?"

**Response**: Complete automation rule with HTTP action for Slack webhook integration.

## 🔧 Technical Details

### Vector Database (ChromaDB)

- **Embedding Model**: `sentence-transformers/all-MiniLM-L6-v2`
- **Chunk Size**: 1000 tokens with 200 token overlap
- **Document Types**: Categorized by automation rules, validation rules, integrations, etc.
- **Storage**: Persistent local storage in `data/chroma_db/`

### Document Processing

The system processes 150+ markdown files including:

- Automation rule examples and configurations
- JavaScript function references  
- Validation rule patterns and DSL syntax
- Integration guides (Slack, GitLab, Wrike)
- Troubleshooting and best practices

### AI Integration

- **Model**: Google Gemini Pro
- **Context Length**: Up to 2048 tokens output
- **Temperature**: 0.7 for balanced creativity and accuracy
- **Retrieval**: Top 5 most relevant documents per query

## 🎯 Query Types

The system supports four main query types:

1. **General Questions** (`general`)
   - Ask anything about automation rules
   - Get explanations of concepts and features

2. **Create Automation** (`create_automation`) 
   - Generate new automation rules from descriptions
   - Get complete JSON configurations

3. **Explain Rule** (`explain_rule`)
   - Understand existing automation or validation rules
   - Get detailed breakdowns of rule components

4. **Improve Rule** (`improve_rule`)
   - Get optimization suggestions for existing rules
   - Learn best practices and enhancements

## 📊 System Statistics

Monitor your system through the web interface or CLI:

- Number of documents in knowledge base
- Gemini API connection status
- Available document types
- Query performance metrics

## 🔍 Advanced Features

### Document Type Filtering

Filter searches by document categories:
- `automation_rules` - Core automation documentation
- `automation_examples` - Example configurations
- `validation_rules` - Validation rule patterns
- `integrations` - External service integrations
- `javascript` - JavaScript API references

### Similarity Threshold

Adjust the similarity threshold (0.1-1.0) to control result relevance:
- Higher values = More strict matching
- Lower values = More lenient matching

### Batch Processing

The system efficiently processes queries in batches and caches results for better performance.

## 🛠️ Development

### Project Structure

- **`src/document_processor.py`**: Handles markdown parsing, text chunking, and embedding generation
- **`src/gemini_client.py`**: Manages Google Gemini API interactions and prompt engineering  
- **`src/rag_system.py`**: Orchestrates the complete RAG pipeline
- **`config/config.py`**: Centralized configuration management

### Extending the System

1. **Add New Document Types**: Update `_categorize_document()` in `document_processor.py`
2. **Custom Prompts**: Modify prompt templates in `gemini_client.py`
3. **New Query Types**: Extend the query routing in `rag_system.py`

## 🔒 Security & Privacy

- API keys stored in environment variables
- Local vector database (no data sent to third parties except Gemini)
- No sensitive information logged
- Rate limiting and error handling included

## 📚 Documentation Coverage

The knowledge base includes comprehensive documentation for:

- **Automation Rules**: 80+ example configurations
- **Validation Rules**: 15+ real-world patterns  
- **JavaScript API**: Complete function reference
- **Integrations**: Slack, GitLab, Wrike, and more
- **Troubleshooting**: Common issues and solutions
- **Best Practices**: Performance and security guidelines

## 🤝 Contributing

Contributions are welcome! Areas for improvement:

- Additional document processors (PDF, Word, etc.)
- More sophisticated chunking strategies
- Additional AI model integrations
- Enhanced web interface features
- Performance optimizations

## 📄 License

This project is provided as-is for educational and development purposes.

## 🆘 Troubleshooting

### Common Issues

1. **"GEMINI_API_KEY not found"**
   - Ensure `.env` file exists with valid API key
   - Check environment variable is set correctly

2. **"No documents found"**
   - Verify markdown files exist in source directory
   - Check path configuration in `config/config.py`

3. **"Vector database error"**
   - Delete `data/chroma_db/` folder and reinitialize
   - Run with `--rebuild` flag

4. **"Gemini API connection failed"**
   - Verify API key is valid and active
   - Check internet connection
   - Ensure you have Gemini API quota available

### Performance Tips

- First initialization takes 2-3 minutes to process all documents
- Subsequent starts are much faster using cached embeddings
- Use document type filters for faster, more relevant results
- Adjust chunk size for different document types

## 📞 Support

For issues and questions:
1. Check the troubleshooting section above
2. Review system logs for error details
3. Verify all dependencies are installed correctly
4. Test with simple queries first

---

**Built with ❤️ using ChromaDB, Sentence Transformers, Google Gemini AI, and Streamlit**