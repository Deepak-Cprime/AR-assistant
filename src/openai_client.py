"""
OpenAI API client for generating responses based on RAG context
"""
import os
from openai import OpenAI
from typing import List, Dict, Any, Optional
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class OpenAIClient:
    def __init__(self, api_key: str, model_name: str = "gpt-4o"):
        """
        Initialize OpenAI client
        """
        self.api_key = api_key
        self.model_name = model_name
        
        if not api_key:
            raise ValueError("OpenAI API key is required")
            
        self.client = OpenAI(api_key=api_key)
        
        # Available models in order of preference
        preferred_models = [
            "gpt-4o",
            "gpt-4-turbo",
            "gpt-4",
            "gpt-3.5-turbo"
        ]
        
        # Use first available preferred model or default
        try:
            models = self.client.models.list()
            available_model_ids = [model.id for model in models.data]
            logger.info(f"Available models: {len(available_model_ids)} models found")
            
            for preferred in preferred_models:
                if preferred in available_model_ids:
                    self.model_name = preferred
                    logger.info(f"Using model: {self.model_name}")
                    break
            else:
                logger.info(f"Using default model: {self.model_name}")
                
        except Exception as e:
            logger.warning(f"Could not list models, using default: {e}")
            self.model_name = model_name
        
        # Configure base generation parameters
        self.base_generation_config = {
            "temperature": 0.7,
            "top_p": 0.9,
            "max_tokens": 2048,
        }
        
    def _get_generation_config(self, complexity_level: str = "medium") -> dict:
        """Get generation parameters based on complexity level"""
        configs = {
            "simple": {
                "temperature": 0.2,  # More deterministic
                "top_p": 0.7,        # Less creative
                "max_tokens": 800,   # Shorter responses
            },
            "medium": {
                "temperature": 0.5,  # Balanced
                "top_p": 0.8,        # Moderate creativity
                "max_tokens": 1500,  # Standard length
            },
            "complex": {
                "temperature": 0.7,  # More creative
                "top_p": 0.9,        # High creativity
                "max_tokens": 2500,  # Longer responses
            }
        }
        return configs.get(complexity_level, configs["medium"])
    
    def _detect_complexity(self, user_query: str, entity_metadata: Dict = None) -> str:
        """Auto-detect complexity level from user query"""
        query_lower = user_query.lower()
        
        # Simple indicators
        simple_keywords = ["create", "when", "if", "simple", "basic"]
        # Complex indicators  
        complex_keywords = ["api", "multiple", "complex", "advanced", "integrate", "fetch", "query"]
        
        simple_score = sum(1 for word in simple_keywords if word in query_lower)
        complex_score = sum(1 for word in complex_keywords if word in query_lower)
        
        # Check if live metadata suggests complexity
        if entity_metadata and len(entity_metadata.get('custom_fields', [])) > 3:
            complex_score += 1
            
        if complex_score > simple_score:
            return "complex"
        elif simple_score > 0:
            return "simple"
        else:
            return "medium"
        
    def generate_automation_rule(self, user_query: str, context_documents: List[Dict], entity_metadata: Dict = None, live_tp_data: Dict = None, complexity_level: str = "auto") -> str:
        """
        Generate automation rule based on user query and retrieved context
        """
        # Auto-detect complexity if needed
        if complexity_level == "auto":
            complexity_level = self._detect_complexity(user_query, entity_metadata)
        
        # Get complexity-specific config
        generation_config = self._get_generation_config(complexity_level)
        
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

IMPORTANT CONTEXT: You are generating JavaScript code that will run INSIDE a TargetProcess automation rule. The `args` object is automatically provided by TargetProcess and contains:
- args.Current: The current entity being processed (UserStory, Bug, etc.)
- args.Previous: The previous state of the entity
- args.ResourceId: ID of the current entity  
- args.ResourceType: Type of the current entity
- args.ChangedFields: Array of fields that changed

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
   - **ALWAYS use args.Current, args.Previous, etc.** - these are automatically available in TargetProcess automation rules

5. **VALIDATE AUTOMATION RULE STRUCTURE**:
   - Every automation rule JavaScript code MUST be a complete function that can reference args
   - Use conditional logic: if (args.Current.SomeField) {{ ... }}
   - Return proper command objects: {{ command: "targetprocess:CreateResource", payload: {{...}} }}
   - Return null if no action needed

6. **BE PRECISE**: Use the exact field names, methods, and patterns demonstrated in the documentation

CRITICAL REQUIREMENTS:
- MUST follow the documentation patterns EXACTLY - do not invent syntax
- JavaScript code must match the style and structure of the provided examples
- Use only the APIs, functions, and patterns shown in the documentation
- **JSON SYNTAX CRITICAL**: In JSON payloads, use string concatenation with + operator: "User Story " + args.Current.Id + " is overdue"
- **NO TEMPLATE LITERALS IN JSON**: Never use backticks (`) in JSON field values - only use them in JavaScript code blocks
- **PROPER QUOTES**: All JSON string values must have double quotes: "Open", not Open
- Ensure the code is properly formatted and copyable in Streamlit

**SYNTAX EXAMPLES FROM DOCUMENTATION:**
✅ CORRECT: Name: "User Story " + args.Current.Id + " exceeds deadline"
❌ WRONG: Name: \`User Story \${{args.Current.Id}} exceeds deadline\`
❌ WRONG: Name: User Story + args.Current.Id + exceeds deadline




"""
        
        try:
            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=[
                    {"role": "system", "content": "You are an expert in TargetProcess automation rules."},
                    {"role": "user", "content": prompt}
                ],
                **generation_config
            )
            return response.choices[0].message.content
        except Exception as e:
            logger.error(f"Error generating response: {e}")
            return f"Error generating response: {str(e)}"
    
    def explain_existing_rule(self, rule_content: str, context_documents: List[Dict]) -> str:
        """
        Explain an existing automation or validation rule
        """
        generation_config = self._get_generation_config("medium")  # Default to medium for explanations
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
            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=[
                    {"role": "system", "content": "You are an expert assistant for Targetprocess automation and validation rules."},
                    {"role": "user", "content": prompt}
                ],
                **generation_config
            )
            return response.choices[0].message.content
        except Exception as e:
            logger.error(f"Error explaining rule: {e}")
            return f"Error explaining rule: {str(e)}"
    
    def suggest_improvements(self, rule_content: str, context_documents: List[Dict]) -> str:
        """
        Suggest improvements for an existing rule
        """
        generation_config = self._get_generation_config("complex")  # Use complex for improvements
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
            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=[
                    {"role": "system", "content": "You are an expert assistant for Targetprocess automation and validation rules."},
                    {"role": "user", "content": prompt}
                ],
                **generation_config
            )
            return response.choices[0].message.content
        except Exception as e:
            logger.error(f"Error suggesting improvements: {e}")
            return f"Error suggesting improvements: {str(e)}"
    
    def answer_question(self, question: str, context_documents: List[Dict]) -> str:
        """
        Answer general questions about automation rules and Targetprocess
        """
        generation_config = self._get_generation_config("medium")  # Default to medium for Q&A
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
            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=[
                    {"role": "system", "content": "You are an expert assistant for Targetprocess automation rules, validation rules, and system configuration."},
                    {"role": "user", "content": prompt}
                ],
                **generation_config
            )
            return response.choices[0].message.content
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
        Test if OpenAI API connection is working
        """
        try:
            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=[{"role": "user", "content": "Hello, this is a test."}],
                max_tokens=10
            )
            return bool(response.choices[0].message.content)
        except Exception as e:
            logger.error(f"OpenAI connection test failed: {e}")
            return False