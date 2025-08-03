"""
Gemini API client for generating responses based on RAG context
"""
import os
import google.generativeai as genai
from typing import List, Dict, Any, Optional
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class GeminiClient:
    def __init__(self, api_key: str, model_name: str = "gemini-2.5-flash"):
        """
        Initialize Gemini client
        """
        self.api_key = api_key
        self.model_name = model_name
        
        if not api_key:
            raise ValueError("Gemini API key is required")
            
        genai.configure(api_key=api_key)
        
        # Try to find the best available model
        try:
            available_models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
            logger.info(f"Available models: {available_models}")
            
            # Preferred models in order
            preferred_models = [
                "models/gemini-2.5-flash",
                "models/gemini-1.5-pro", 
                "models/gemini-pro",
                "models/gemini-1.0-pro"
            ]
            
            # Use the first available preferred model
            for preferred in preferred_models:
                if preferred in available_models:
                    self.model_name = preferred
                    logger.info(f"Using model: {self.model_name}")
                    break
            else:
                # Use the first available model if none of the preferred ones are available
                if available_models:
                    self.model_name = available_models[0]
                    logger.info(f"Using first available model: {self.model_name}")
                
        except Exception as e:
            logger.warning(f"Could not list models, using default: {e}")
            self.model_name = "models/gemini-2.5-flash"
        
        self.model = genai.GenerativeModel(self.model_name)
        
        # Configure generation parameters
        self.generation_config = genai.types.GenerationConfig(
            temperature=0.7,
            top_p=0.9,
            top_k=40,
            max_output_tokens=2048,
        )
        
    def generate_automation_rule(self, user_query: str, context_documents: List[Dict], entity_metadata: Dict = None, live_tp_data: Dict = None) -> str:
        """
        Generate automation rule based on user query and retrieved context
        """
        context_text = self._format_context(context_documents)
        
        # Add live TargetProcess metadata context
        metadata_text = ""
        if entity_metadata:
            metadata_text = f"""
LIVE TARGETPROCESS METADATA (Use these exact field names and values):
- Entity Type: {entity_metadata.get('entity_type', 'Unknown')}
- Available Standard Fields: {', '.join(entity_metadata.get('standard_fields', []))}
- Available Custom Fields: {', '.join(entity_metadata.get('custom_fields', []))}
- Available States: {', '.join(entity_metadata.get('states', []))}
- State Details: {entity_metadata.get('process_states', [])}
- Data Source: {entity_metadata.get('source', 'live_api')}
"""

        # Add additional live context if available
        live_context_text = ""
        if live_tp_data:
            live_context_text = f"""
CURRENT TARGETPROCESS CONTEXT:
- Page Context: {live_tp_data.get('context_type', 'unknown')}
- Current Page: {live_tp_data.get('current_page_context', {}).get('url', 'N/A')}
- Field Access Patterns: Available for JavaScript generation
- Real-time Data: This is live data from your TargetProcess instance
"""
        
        prompt = f"""
You are an expert in Targetprocess automation rules. Your task is to create a working automation rule with a STRUCTURED, CONCISE format for a Chrome extension floating widget.

{metadata_text}

{live_context_text}

WORKING EXAMPLES AND DOCUMENTATION:
{context_text}

USER REQUEST: {user_query}

RESPONSE FORMAT REQUIREMENTS:
Your response MUST follow this EXACT TargetProcess Rule Editor format:

RULE CONFIGURATION:
═══════════════════════════════════════════════════════════════════

📋 RULE NAME: [Descriptive name for the automation rule]

🎯 WHEN:
   Entity: [UserStory|Bug|Feature|Task|Epic|etc.]
   Action: [ ] Created  [ ] Updated  [ ] Deleted
   
   Field Conditions:
   ┌─────────────────────────────────────────────────────────────┐
   │ Field: [FieldName]                                          │
   │ Condition: [equals/not equals/contains/changed to/etc.]     │
   │ Value: [specific value or condition]                        │
   └─────────────────────────────────────────────────────────────┘

🔧 THEN:
   Action Type: Execute JavaScript

**JavaScript Code:**
```javascript
[Complete JavaScript automation code based on the provided documentation examples]
```

📝 DESCRIPTION:
   [Brief description of what this rule does]

═══════════════════════════════════════════════════════════════════

INSTRUCTIONS:
1. **ANALYZE THE PROVIDED DOCUMENTATION THOROUGHLY**: The context contains real TargetProcess automation rule examples and patterns. Study them carefully to understand:
   - The exact JavaScript syntax and API calls used
   - How entities are accessed and manipulated
   - Field naming conventions and reference patterns
   - Error handling and best practices

2. **FOLLOW THE DOCUMENTATION PATTERNS EXACTLY**: 
   - Use the SAME JavaScript syntax as shown in the examples
   - Use the SAME API calls and helper functions
   - Use the SAME field access patterns
   - Use the SAME entity creation/update patterns

3. **MARK THE CORRECT TRIGGER**: Use [✓] for the applicable trigger based on the user's request

4. **GENERATE COMPLETE, WORKING CODE**: 
   - Base your JavaScript code on the patterns found in the documentation
   - Ensure the code is complete and functional
   - Use proper error handling as shown in examples
   - Follow the exact syntax patterns from the provided examples

5. **BE PRECISE**: Use the exact field names, methods, and patterns demonstrated in the documentation

CRITICAL REQUIREMENTS:
- MUST follow the documentation patterns EXACTLY - do not invent syntax
- JavaScript code must match the style and structure of the provided examples
- Use only the APIs, functions, and patterns shown in the documentation
- Ensure the code is properly formatted and copyable in Streamlit
"""
        
        try:
            response = self.model.generate_content(
                prompt,
                generation_config=self.generation_config
            )
            return response.text
        except Exception as e:
            logger.error(f"Error generating response: {e}")
            return f"Error generating response: {str(e)}"
    
    def explain_existing_rule(self, rule_content: str, context_documents: List[Dict]) -> str:
        """
        Explain an existing automation or validation rule
        """
        context_text = self._format_context(context_documents)
        
        prompt = f"""
You are an expert assistant for Targetprocess automation and validation rules.
Based on the provided documentation context, explain the following rule in detail.

CONTEXT DOCUMENTATION:
{context_text}

RULE TO EXPLAIN:
{rule_content}

Please provide:
1. What this rule does (purpose and functionality)
2. When it triggers (source/trigger conditions)
3. What conditions must be met (filters/validation conditions)
4. What actions it performs
5. Potential use cases and benefits
6. Any limitations or considerations

Make the explanation clear and accessible for both technical and non-technical users.
"""
        
        try:
            response = self.model.generate_content(
                prompt,
                generation_config=self.generation_config
            )
            return response.text
        except Exception as e:
            logger.error(f"Error explaining rule: {e}")
            return f"Error explaining rule: {str(e)}"
    
    def suggest_improvements(self, rule_content: str, context_documents: List[Dict]) -> str:
        """
        Suggest improvements for an existing rule
        """
        context_text = self._format_context(context_documents)
        
        prompt = f"""
You are an expert assistant for Targetprocess automation and validation rules.
Based on the provided documentation context, analyze the following rule and suggest improvements.

CONTEXT DOCUMENTATION:
{context_text}

RULE TO IMPROVE:
{rule_content}

Please provide:
1. Analysis of the current rule
2. Potential improvements for performance
3. Enhanced error handling suggestions
4. Better filtering options
5. Additional functionality that could be added
6. Best practices that could be applied
7. Updated/improved rule configuration

Focus on practical, implementable improvements.
"""
        
        try:
            response = self.model.generate_content(
                prompt,
                generation_config=self.generation_config
            )
            return response.text
        except Exception as e:
            logger.error(f"Error suggesting improvements: {e}")
            return f"Error suggesting improvements: {str(e)}"
    
    def answer_question(self, question: str, context_documents: List[Dict]) -> str:
        """
        Answer general questions about automation rules and Targetprocess
        """
        context_text = self._format_context(context_documents)
        
        prompt = f"""
You are an expert assistant for Targetprocess automation rules, validation rules, and system configuration.
Your goal is to provide accurate answers based STRICTLY on the provided documentation.

CONTEXT DOCUMENTATION:
{context_text}

USER QUESTION: {question}

INSTRUCTIONS:
1. **BASE YOUR ANSWER ON THE DOCUMENTATION**: Use only information and patterns shown in the provided context
2. **PROVIDE EXACT EXAMPLES**: When showing code or configurations, copy the exact syntax from the documentation
3. **FOLLOW ESTABLISHED PATTERNS**: If showing automation rules, use the same structure and syntax as the examples
4. **BE PRECISE WITH SYNTAX**: Use exact API calls, object structures, and command patterns from the docs
5. **CITE YOUR SOURCES**: Reference which document or example you're using

RESPONSE FORMAT:
1. **Direct Answer**: Clear response to the question
2. **Working Example**: If applicable, provide exact code/configuration from the documentation 
3. **Step-by-Step Guide**: Based on the documentation patterns
4. **Related Information**: Other relevant concepts from the provided context
5. **Source References**: Which documents provided this information

CRITICAL: Only use syntax, structures, and examples that appear in the provided documentation. Do not invent or assume syntax not shown in the context.
"""
        
        try:
            response = self.model.generate_content(
                prompt,
                generation_config=self.generation_config
            )
            return response.text
        except Exception as e:
            logger.error(f"Error answering question: {e}")
            return f"Error answering question: {str(e)}"
    
    def _format_context(self, context_documents: List[Dict]) -> str:
        """
        Format retrieved documents into context string
        """
        if not context_documents:
            return "No relevant documentation found."
        
        formatted_context = []
        for i, doc in enumerate(context_documents, 1):
            metadata = doc.get('metadata', {})
            content = doc.get('content', '')
            
            section = f"""
--- Document {i}: {metadata.get('title', 'Unknown')} ---
File: {metadata.get('file_name', 'Unknown')}
Type: {metadata.get('doc_type', 'general')}
Content:
{content}
"""
            formatted_context.append(section)
        
        return "\n".join(formatted_context)
    
    def test_connection(self) -> bool:
        """
        Test if Gemini API connection is working
        """
        try:
            response = self.model.generate_content("Hello, this is a test.")
            return bool(response.text)
        except Exception as e:
            logger.error(f"Gemini connection test failed: {e}")
            return False