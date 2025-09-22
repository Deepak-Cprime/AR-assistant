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
        
        # Configure base generation parameters (updated for better accuracy)
        self.base_generation_config = {
            "temperature": 0.3,  # Lower for less hallucination
            "top_p": 0.8,        # More focused
            "max_tokens": 2048,
        }
        
    def _get_generation_config(self, complexity_level: str = "medium") -> dict:
        """Get generation parameters based on complexity level - updated for anti-hallucination"""
        configs = {
            "simple": {
                "temperature": 0.1,  # More deterministic - reduced from 0.2
                "top_p": 0.7,        # Less creative
                "max_tokens": 800,   # Shorter responses
            },
            "medium": {
                "temperature": 0.2,  # More deterministic - reduced from 0.5
                "top_p": 0.8,        # Moderate creativity
                "max_tokens": 1500,  # Standard length
            },
            "complex": {
                "temperature": 0.3,  # More controlled - reduced from 0.7
                "top_p": 0.9,        # High creativity
                "max_tokens": 2500,  # Longer responses
            },
            "agentic": {
                "temperature": 0.2,  # Moderate for multi-agent coordination
                "top_p": 0.8,        # Balanced creativity for agent system
                "max_tokens": 2000,  # Standard length for agent processing
            }
        }
        return configs.get(complexity_level, configs["medium"])
    
        
    # OLD COMPLEX PROMPT METHOD - COMMENTED OUT BUT KEPT FOR REFERENCE
    def generate_automation_rule_old(self, user_query: str, context_documents: List[Dict], entity_metadata: Dict = None, sample_entity_data: Dict = None, complexity_level: str = "auto") -> str:
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

        # Add sample entity data context if available
        sample_context_text = ""
        if sample_entity_data and sample_entity_data.get('sample_data'):
            sample_data = sample_entity_data['sample_data']
            access_patterns = sample_entity_data.get('access_patterns', {})
            
            # Build example field values
            field_examples = []
            for field, pattern in access_patterns.items():
                if field in sample_data:
                    value = sample_data[field]
                    if isinstance(value, dict) and 'Name' in value:
                        field_examples.append(f"- {field}: {pattern} = \"{value['Name']}\"")
                    elif isinstance(value, dict) and 'Id' in value:
                        field_examples.append(f"- {field}: {pattern} = {value['Id']}")
                    elif not isinstance(value, (dict, list)):
                        field_examples.append(f"- {field}: {pattern} = \"{value}\"")
            
            sample_context_text = f"""
REAL EXAMPLE FROM YOUR TARGETPROCESS INSTANCE:
Entity: {sample_data.get('Name', 'Sample')} (ID: {sample_data.get('Id', 'N/A')})
Type: {sample_entity_data.get('entity_type', 'Unknown')}
Source: {sample_entity_data.get('source', 'unknown')}

JAVASCRIPT ACCESS PATTERNS (Use these exact patterns):
{chr(10).join(field_examples[:8])}  

SAMPLE FIELD VALUES:
- Current Priority: {sample_data.get('Priority', {}).get('Name', 'N/A')}
- Current Owner: {sample_data.get('Owner', {}).get('Name', 'N/A')}
- Current State: {sample_data.get('EntityState', {}).get('Name', 'N/A')}
- Project: {sample_data.get('Project', {}).get('Name', 'N/A')}

IMPORTANT: Use these EXACT access patterns in your generated JavaScript code.
"""
        
        prompt = f"""
You are an automation rule generator for TargetProcess. Follow the Plan & Execute methodology:

## PLAN PHASE
Analyze the user request and create:
1. **Business Logic Chain**: Trigger → Condition → Action → Outcome
2. **Entity Flow**: Map which entities are involved and how they relate
3. **Validation Requirements**: What conditions must be met
4. **Success Criteria**: Expected outcomes

## EXECUTE PHASE  
Generate implementation:
1. **Pipeline Configuration**: JSON config for triggers and filters
2. **JavaScript Code**: Implementation logic with proper API usage
3. **Error Handling**: Logging and exception management
4. **Documentation**: Clear explanation of the rule

## CONTEXT USAGE
Use retrieved RAG examples to:
- Find similar patterns for business logic
- Reuse proven code patterns and API calls
- Ensure consistent error handling and logging
- Follow established naming conventions

IMPORTANT CONTEXT: You are generating JavaScript code that will run INSIDE a TargetProcess automation rule. The `args` object is automatically provided by TargetProcess and contains:
- args.Current: The current entity being processed (UserStory, Bug, etc.)
- args.Previous: The previous state of the entity
- args.ResourceId: ID of the current entity  
- args.ResourceType: Type of the current entity
- args.ChangedFields: Array of fields that changed

{metadata_text}

{sample_context_text}

WORKING EXAMPLES AND DOCUMENTATION:
{context_text}

USER REQUEST: {user_query}

## PLAN PHASE ANALYSIS:

**Step 1: Business Logic Chain**
Analyze: {user_query}
- Trigger: [Identify what event starts this rule]
- Condition: [What conditions must be met]
- Action: [What should happen]
- Outcome: [Expected result]

**Step 2: Entity Flow**
Map entities involved:
- Primary Entity: [Main entity being processed]
- Related Entities: [Connected entities that may be affected]
- Data Flow: [How information flows between entities]

**Step 3: Validation Requirements**
Identify constraints:
- Field validations needed
- Business rule constraints
- Data integrity checks

**Step 4: Success Criteria**
Define expected outcomes:
- What indicates successful execution
- How to measure rule effectiveness
- Error conditions to handle

## EXECUTE PHASE IMPLEMENTATION:

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

🔍 BUSINESS LOGIC ANALYSIS:
   - Trigger: [What starts this rule]
   - Flow: [Entity relationships and data flow]
   - Validation: [What conditions are checked]
   - Outcome: [Expected results]

═══════════════════════════════════════════════════════════════════

EXECUTION INSTRUCTIONS:
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

3. **IMPLEMENT PLAN & EXECUTE METHODOLOGY**:
   - First analyze the business logic chain
   - Map entity relationships and data flow
   - Identify validation requirements
   - Define success criteria
   - Then generate complete implementation

4. **GENERATE COMPLETE, WORKING CODE**: 
   - Base your JavaScript code on the patterns found in the documentation
   - Ensure the code is complete and functional
   - Use proper error handling as shown in examples
   - Follow the exact syntax patterns from the provided examples
   - **ALWAYS use args.Current, args.Previous, etc.** - these are automatically available in TargetProcess automation rules

5. **VALIDATE AUTOMATION RULE STRUCTURE**:
   - Every automation rule JavaScript code MUST be a complete function that can reference args
   - Use conditional logic: if (args.Current.SomeField) {{ ... }}
   - Return null if no action needed

6. **ENSURE COMPREHENSIVE ERROR HANDLING**:
   - Log meaningful error messages
   - Handle edge cases and null values
   - Provide fallback behaviors

CRITICAL REQUIREMENTS:
- MUST follow the documentation patterns EXACTLY - do not invent syntax
- JavaScript code must match the style and structure of the provided examples
- Use only the APIs, functions, and patterns shown in the documentation
- **JSON SYNTAX CRITICAL**: In JSON payloads, use string concatenation with + operator: "User Story " + args.Current.Id + " is overdue"
- **NO TEMPLATE LITERALS IN JSON**: Never use backticks (`) in JSON field values - only use them in JavaScript code blocks
- **PROPER QUOTES**: All JSON string values must have double quotes: "Open", not Open
- Generate the complete automation rule following the exact format and syntax from the retrieved examples



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

    def generate_automation_rule(self, user_query: str, context_documents: List[Dict], entity_metadata: Dict = None, sample_entity_data: Dict = None, complexity_level: str = "auto") -> str:
        """
        NEW IMPROVED ANTI-HALLUCINATION PROMPT - Generate automation rule with improved accuracy
        Based on improvements.md recommendations for constraint-based prompting
        """
        # Auto-detect complexity if needed
        if complexity_level == "auto":
            complexity_level = self._detect_complexity(user_query, entity_metadata)

        generation_config = self._get_generation_config(complexity_level)
        context_text = self._format_context(context_documents)

        # Build metadata context more concisely
        metadata_context = ""
        if entity_metadata:
            metadata_context = f"""
AVAILABLE FIELDS (use these exact names):
- Entity: {entity_metadata.get('entity_type')}
- Fields: {', '.join(entity_metadata.get('standard_fields', [])[:10])}
- Custom: {', '.join(entity_metadata.get('custom_fields', [])[:5])}
- States: {', '.join(entity_metadata.get('states', [])[:8])}
"""

        # Build sample data context more focused
        sample_context = ""
        if sample_entity_data and sample_entity_data.get('sample_data'):
            sample_data = sample_entity_data['sample_data']
            access_patterns = sample_entity_data.get('access_patterns', {})

            # Show only the most relevant field examples
            key_examples = []
            priority_fields = ['Name', 'Id', 'EntityState', 'Priority', 'Owner', 'Project']

            for field in priority_fields:
                if field in access_patterns and field in sample_data:
                    pattern = access_patterns[field]
                    value = sample_data[field]
                    if isinstance(value, dict) and 'Name' in value:
                        key_examples.append(f"{pattern} = \"{value['Name']}\"")
                    elif isinstance(value, dict) and 'Id' in value:
                        key_examples.append(f"{pattern} = {value['Id']}")

            sample_context = f"""
FIELD ACCESS PATTERNS (use exactly):
{chr(10).join(key_examples[:6])}
"""

        # Simplified, focused prompt based on improvements.md
        prompt = f"""You are a TargetProcess automation rule generator. Generate ONLY working code based on provided examples.

CONSTRAINT: You MUST follow the exact patterns from the provided examples. Do NOT invent syntax.

{metadata_context}
{sample_context}

EXAMPLES AND PATTERNS:
{context_text}

USER REQUEST: {user_query}

RESPONSE FORMAT (follow exactly):

📋 RULE: [Brief name]

🎯 TRIGGER:
Entity: [Type from metadata]
Event: [Created/Updated/Deleted based on request]
Conditions: [Specific field conditions if any]

🔧 JAVASCRIPT:
```javascript
[Complete working code following the exact patterns from examples above.
- Use args.Current, args.Previous, args.ResourceId as shown in examples
- Copy API call patterns exactly from examples
- Use same error handling patterns from examples
- Return commands array or null as shown in examples]
```

CRITICAL RULES:
1. Copy JavaScript syntax EXACTLY from the provided examples
2. Use only API calls and patterns shown in examples
3. Use args.Current.FieldName pattern for field access
4. Return commands array for actions, null for no-op
5. No template literals in JSON strings - use string concatenation
6. All JSON values must have double quotes

Generate complete, working automation rule now:"""

        try:
            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=[
                    {"role": "system", "content": "You generate TargetProcess automation rules. Follow provided examples exactly. Never invent syntax."},
                    {"role": "user", "content": prompt}
                ],
                **generation_config
            )
            
            # Validate the generated code
            generated_code = response.choices[0].message.content
            is_valid, issues = self.validate_generated_code(generated_code)
            
            if not is_valid:
                logger.warning(f"Generated code validation issues: {issues}")
                # Could implement retry logic here if needed
            
            return generated_code
        except Exception as e:
            logger.error(f"Error generating response: {e}")
            return f"Error generating response: {str(e)}"

    def validate_generated_code(self, generated_code: str) -> tuple:
        """
        Validate generated code against known patterns - from improvements.md recommendations
        """
        issues = []
        
        # Check for template literals in JSON context
        if '`' in generated_code and '"' in generated_code:
            # More sophisticated check - look for backticks inside JSON-like structures
            lines = generated_code.split('\n')
            for i, line in enumerate(lines):
                if '`' in line and ('{' in line or '}' in line or '"' in line):
                    issues.append(f"Line {i+1}: Template literals found in JSON context")
        
        # Check for args usage
        if 'args.Current' not in generated_code and 'args.' not in generated_code:
            issues.append("Missing args object usage")
        
        # Check for proper API patterns
        has_api_calls = any(pattern in generated_code for pattern in [
            'api.queryAsync', 'utils.createResource', 'tp.api', 'fetch'
        ])
        if not has_api_calls and 'javascript' in generated_code.lower():
            issues.append("Missing proper API calls")
        
        # Check for proper return structure
        if 'return ' not in generated_code and 'javascript' in generated_code.lower():
            issues.append("Missing return statement")
        
        # Try-catch is optional - removed requirement
        
        # Check for double quotes in JSON (common issue)
        if "'" in generated_code and '{' in generated_code:
            issues.append("Single quotes detected - use double quotes in JSON")
        
        return len(issues) == 0, issues
    
    def explain_existing_rule(self, rule_content: str, context_documents: List[Dict]) -> str:
        """
        Explain an existing automation or validation rule
        """
        generation_config = self._get_generation_config("simple")  # Use simple for more focused explanations
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
        generation_config = self._get_generation_config("medium")  # Use medium for balanced improvements
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
        generation_config = self._get_generation_config("simple")  # Use simple for more focused Q&A
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