"""
Agentic RAG System - Multi-step reasoning and retrieval for complex automation rules
Implements planning, specialized retrieval, validation, and refinement agents
"""
import os
from typing import List, Dict, Any, Optional, Tuple
import logging
from datetime import datetime
import json
import re

from .openai_client import OpenAIClient

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class QueryPlanningAgent:
    """Agent responsible for decomposing complex queries into sub-tasks"""
    
    def __init__(self, openai_client: OpenAIClient):
        self.openai_client = openai_client
        
    def plan_query(self, user_query: str, tp_context: Dict = None) -> Dict:
        """
        Analyze query and create execution plan
        """
        planning_prompt = f"""
You are a query planning agent for TargetProcess automation rules. Analyze the user request and create a structured execution plan.

USER REQUEST: {user_query}

CONTEXT: {tp_context if tp_context else 'No additional context provided'}

Create a JSON response with the following structure:
{{
    "complexity": "simple|medium|complex",
    "entity_focus": "primary entity type (UserStory, Bug, Feature, Task, etc.)",
    "sub_tasks": [
        {{
            "task": "brief description",
            "search_focus": "what to search for",
            "priority": 1-5
        }}
    ],
    "retrieval_strategy": {{
        "code_patterns": true/false,
        "entity_metadata": true/false,
        "business_logic": true/false,
        "error_handling": true/false
    }},
    "validation_requirements": [
        "field name validation",
        "syntax validation",
        "business logic validation"
    ]
}}

ANALYSIS GUIDELINES:
- Simple: Single entity, basic trigger/action (Create X when Y)
- Medium: Multiple conditions, field mappings, state changes
- Complex: Multiple entities, API calls, complex business logic, integrations

- Identify the PRIMARY entity that triggers the automation
- Break down into logical sub-tasks (usually 2-4 tasks)
- Determine what types of information need to be retrieved
- List what validations will be needed

Respond with ONLY the JSON structure:"""

        try:
            response = self.openai_client.client.chat.completions.create(
                model=self.openai_client.model_name,
                messages=[
                    {"role": "system", "content": "You are a query planning agent. Always respond with valid JSON only."},
                    {"role": "user", "content": planning_prompt}
                ],
                temperature=0.1,
                max_tokens=800
            )
            
            plan_text = response.choices[0].message.content.strip()
            
            # Try to parse JSON with robust extraction
            try:
                # Extract JSON from response (handle cases where AI adds explanatory text)
                json_text = self._extract_json_from_response(plan_text)
                plan = json.loads(json_text)
                logger.info(f"Query plan created: {plan['complexity']} complexity, {len(plan['sub_tasks'])} sub-tasks")
                return plan
            except json.JSONDecodeError as e:
                logger.warning(f"Failed to parse planning response as JSON: {e}")
                logger.debug(f"Raw response: {plan_text[:200]}...")
                return self._create_fallback_plan(user_query)
                
        except Exception as e:
            logger.error(f"Error in query planning: {e}")
            return self._create_fallback_plan(user_query)
    
    def _extract_json_from_response(self, response_text: str) -> str:
        """Extract JSON from AI response, handling cases with explanatory text"""
        # Look for JSON object boundaries
        start_idx = response_text.find('{')
        if start_idx == -1:
            raise json.JSONDecodeError("No JSON object found", response_text, 0)
        
        # Find the matching closing brace
        brace_count = 0
        end_idx = start_idx
        
        for i in range(start_idx, len(response_text)):
            if response_text[i] == '{':
                brace_count += 1
            elif response_text[i] == '}':
                brace_count -= 1
                if brace_count == 0:
                    end_idx = i
                    break
        
        if brace_count != 0:
            raise json.JSONDecodeError("Unmatched braces in JSON", response_text, start_idx)
        
        json_text = response_text[start_idx:end_idx + 1]
        
        # Clean common JSON issues
        json_text = self._clean_json_text(json_text)
        
        return json_text
    
    def _clean_json_text(self, json_text: str) -> str:
        """Clean common JSON formatting issues"""
        # Remove trailing commas before closing braces/brackets
        json_text = re.sub(r',(\s*[}\]])', r'\1', json_text)
        
        # Fix unquoted keys (basic fix)
        json_text = re.sub(r'(\w+)(:)', r'"\1"\2', json_text)
        
        # Remove duplicate quotes
        json_text = re.sub(r'""(\w+)""', r'"\1"', json_text)
        
        return json_text
    
    def _create_fallback_plan(self, user_query: str) -> Dict:
        """Create a basic plan when AI planning fails"""
        return {
            "complexity": "medium",
            "entity_focus": "UserStory",
            "sub_tasks": [
                {"task": "Find automation patterns", "search_focus": "automation rules javascript", "priority": 1},
                {"task": "Get entity information", "search_focus": "entity fields properties", "priority": 2},
                {"task": "Find business logic", "search_focus": "workflow triggers conditions", "priority": 3}
            ],
            "retrieval_strategy": {
                "code_patterns": True,
                "entity_metadata": True,
                "business_logic": True,
                "error_handling": True
            },
            "validation_requirements": ["field name validation", "syntax validation"]
        }

class SpecializedRetrievalAgent:
    """Agent that performs multiple specialized retrieval rounds"""
    
    def __init__(self, vector_db):
        self.vector_db = vector_db
        
    def multi_step_retrieve(self, plan: Dict, user_query: str, max_results: int = 8) -> Dict[str, List[Dict]]:
        """
        Perform specialized retrieval based on plan
        """
        retrieval_results = {}
        strategy = plan.get('retrieval_strategy', {})
        entity_focus = plan.get('entity_focus', '')
        
        logger.info(f"Starting multi-step retrieval with strategy: {strategy}")
        
        # Round 1: Code Patterns
        if strategy.get('code_patterns', False):
            code_queries = [
                f"{user_query} javascript automation",
                f"{entity_focus} automation rule code",
                "javascript args.Current api calls",
                "automation rule javascript patterns"
            ]
            
            code_docs = []
            for query in code_queries:
                docs = self.vector_db.search(query=query, n_results=max_results//4)
                code_docs.extend(docs)
            
            retrieval_results['code_patterns'] = self._deduplicate_docs(code_docs)[:max_results//2]
            logger.info(f"Code patterns retrieved: {len(retrieval_results['code_patterns'])} docs")
        
        # Round 2: Entity Metadata
        if strategy.get('entity_metadata', False):
            entity_queries = [
                f"{entity_focus} fields properties metadata",
                f"{entity_focus} entity structure",
                "entity fields access patterns",
                f"{entity_focus} state transitions"
            ]
            
            entity_docs = []
            for query in entity_queries:
                docs = self.vector_db.search(query=query, n_results=max_results//4)
                entity_docs.extend(docs)
                
            retrieval_results['entity_metadata'] = self._deduplicate_docs(entity_docs)[:max_results//2]
            logger.info(f"Entity metadata retrieved: {len(retrieval_results['entity_metadata'])} docs")
        
        # Round 3: Business Logic
        if strategy.get('business_logic', False):
            business_queries = [
                f"{user_query} workflow automation",
                f"{user_query} business rules",
                "automation triggers conditions",
                "workflow state transitions"
            ]
            
            business_docs = []
            for query in business_queries:
                docs = self.vector_db.search(query=query, n_results=max_results//4)
                business_docs.extend(docs)
                
            retrieval_results['business_logic'] = self._deduplicate_docs(business_docs)[:max_results//2]
            logger.info(f"Business logic retrieved: {len(retrieval_results['business_logic'])} docs")
        
        # Round 4: Error Handling
        if strategy.get('error_handling', False):
            error_queries = [
                "error handling automation rules",
                "try catch javascript automation",
                "validation error handling",
                "null check automation rules"
            ]
            
            error_docs = []
            for query in error_queries:
                docs = self.vector_db.search(query=query, n_results=max_results//4)
                error_docs.extend(docs)
                
            retrieval_results['error_handling'] = self._deduplicate_docs(error_docs)[:max_results//2]
            logger.info(f"Error handling retrieved: {len(retrieval_results['error_handling'])} docs")
        
        return retrieval_results
    
    def _deduplicate_docs(self, docs: List[Dict]) -> List[Dict]:
        """Remove duplicate documents based on content similarity"""
        seen_content = set()
        unique_docs = []
        
        for doc in docs:
            content = doc.get('content', '')
            # Use first 100 characters as deduplication key
            content_key = content[:100].strip()
            
            if content_key not in seen_content:
                seen_content.add(content_key)
                unique_docs.append(doc)
        
        return unique_docs

class ContextSynthesisAgent:
    """Agent that synthesizes retrieval results into focused context"""
    
    def __init__(self, openai_client: OpenAIClient):
        self.openai_client = openai_client
        
    def synthesize_context(self, retrieval_results: Dict[str, List[Dict]], plan: Dict, user_query: str) -> Dict:
        """
        Synthesize multiple retrieval results into focused context sets
        """
        logger.info("Synthesizing context from retrieval results")
        
        # Combine all retrieved docs
        all_docs = []
        for category, docs in retrieval_results.items():
            for doc in docs:
                doc_copy = doc.copy()
                doc_copy['retrieval_category'] = category
                all_docs.append(doc_copy)
        
        # Rank by relevance and retrieval category priority
        ranked_docs = self._rank_by_relevance(all_docs, user_query, plan)
        
        # Create focused context sets
        context_sets = {
            'primary_context': ranked_docs[:8],  # Most relevant docs
            'code_examples': [doc for doc in ranked_docs if 'javascript' in doc.get('content', '').lower()][:5],
            'entity_info': [doc for doc in ranked_docs if doc.get('retrieval_category') == 'entity_metadata'][:3],
            'business_patterns': [doc for doc in ranked_docs if doc.get('retrieval_category') == 'business_logic'][:3]
        }
        
        logger.info(f"Context synthesis complete: {len(context_sets['primary_context'])} primary docs, "
                   f"{len(context_sets['code_examples'])} code examples")
        
        return context_sets
    
    def _rank_by_relevance(self, docs: List[Dict], user_query: str, plan: Dict) -> List[Dict]:
        """Rank documents by relevance to query and plan"""
        query_keywords = set(user_query.lower().split())
        entity_focus = plan.get('entity_focus', '').lower()
        
        for doc in docs:
            relevance_score = 0
            content = doc.get('content', '').lower()
            category = doc.get('retrieval_category', '')
            
            # Keyword matching
            content_keywords = set(content.split())
            keyword_overlap = len(query_keywords.intersection(content_keywords))
            relevance_score += keyword_overlap * 0.5
            
            # Entity focus bonus
            if entity_focus and entity_focus in content:
                relevance_score += 2
            
            # Code pattern bonus
            if 'javascript' in content and 'args.current' in content:
                relevance_score += 3
            
            # Category priority
            category_weights = {
                'code_patterns': 3,
                'entity_metadata': 2,
                'business_logic': 2,
                'error_handling': 1
            }
            relevance_score += category_weights.get(category, 0)
            
            # Distance penalty (lower distance = higher similarity)
            distance = doc.get('distance', 1.0)
            relevance_score += (1.0 - distance) * 2
            
            doc['relevance_score'] = relevance_score
        
        return sorted(docs, key=lambda x: x.get('relevance_score', 0), reverse=True)

class ValidationAgent:
    """Agent that validates generated automation rules"""
    
    def __init__(self, openai_client: OpenAIClient):
        self.openai_client = openai_client
        
    def validate_rule(self, generated_rule: str, context_docs: List[Dict], plan: Dict) -> Tuple[bool, List[str], Dict]:
        """
        Validate generated automation rule against patterns and requirements
        """
        issues = []
        validation_details = {}
        
        logger.info("Starting rule validation")
        
        # Syntax validation
        syntax_issues = self._validate_syntax(generated_rule)
        issues.extend(syntax_issues)
        validation_details['syntax'] = len(syntax_issues) == 0
        
        # Pattern validation
        pattern_issues = self._validate_patterns(generated_rule, context_docs)
        issues.extend(pattern_issues)
        validation_details['patterns'] = len(pattern_issues) == 0
        
        # Business logic validation
        logic_issues = self._validate_business_logic(generated_rule, plan)
        issues.extend(logic_issues)
        validation_details['business_logic'] = len(logic_issues) == 0
        
        # Field validation (basic)
        field_issues = self._validate_fields(generated_rule)
        issues.extend(field_issues)
        validation_details['fields'] = len(field_issues) == 0
        
        is_valid = len(issues) == 0
        validation_details['total_issues'] = len(issues)
        validation_details['is_valid'] = is_valid
        
        logger.info(f"Validation complete: {'PASSED' if is_valid else 'FAILED'} with {len(issues)} issues")
        
        return is_valid, issues, validation_details
    
    def _validate_syntax(self, rule: str) -> List[str]:
        """Validate JavaScript syntax patterns"""
        issues = []
        
        # Check for template literals in JSON contexts
        if '`' in rule and '"' in rule:
            lines = rule.split('\n')
            for i, line in enumerate(lines):
                if '`' in line and ('{' in line or '}' in line):
                    issues.append(f"Line {i+1}: Template literals found in JSON context")
        
        # Check for args usage
        if 'args.Current' not in rule and 'args.' not in rule and 'javascript' in rule.lower():
            issues.append("Missing args object usage in JavaScript code")
        
        # Check for return statement
        if 'return ' not in rule and 'javascript' in rule.lower():
            issues.append("Missing return statement in JavaScript code")
        
        return issues
    
    def _validate_patterns(self, rule: str, context_docs: List[Dict]) -> List[str]:
        """Validate against known patterns from context"""
        issues = []
        
        # Extract common API patterns from context
        api_patterns = set()
        for doc in context_docs:
            content = doc.get('content', '')
            # Look for API calls
            api_matches = re.findall(r'(api\.\w+|utils\.\w+|tp\.\w+)', content, re.IGNORECASE)
            api_patterns.update(api_matches)
        
        # Check if generated rule uses known API patterns
        if api_patterns and 'javascript' in rule.lower():
            has_known_api = any(pattern.lower() in rule.lower() for pattern in api_patterns)
            if not has_known_api:
                issues.append("Generated code doesn't use known API patterns from examples")
        
        return issues
    
    def _validate_business_logic(self, rule: str, plan: Dict) -> List[str]:
        """Validate business logic consistency"""
        issues = []
        
        entity_focus = plan.get('entity_focus', '')
        if entity_focus and entity_focus.lower() not in rule.lower():
            issues.append(f"Generated rule doesn't reference expected entity type: {entity_focus}")
        
        return issues
    
    def _validate_fields(self, rule: str) -> List[str]:
        """Basic field validation"""
        issues = []
        
        # Check for common field access patterns
        if 'args.Current.' in rule:
            # Extract field names
            field_matches = re.findall(r'args\.Current\.(\w+)', rule)
            if not field_matches:
                issues.append("Found args.Current usage but no field access patterns")
        
        return issues

class RefinementAgent:
    """Agent that refines rules based on validation issues"""
    
    def __init__(self, openai_client: OpenAIClient):
        self.openai_client = openai_client
        
    def refine_rule(self, original_rule: str, issues: List[str], context_docs: List[Dict], user_query: str, max_attempts: int = 2) -> str:
        """
        Refine rule based on validation issues
        """
        logger.info(f"Starting rule refinement with {len(issues)} issues")
        
        if not issues:
            return original_rule
        
        refined_rule = original_rule
        
        for attempt in range(max_attempts):
            logger.info(f"Refinement attempt {attempt + 1}/{max_attempts}")
            
            refinement_prompt = f"""
You are a rule refinement agent. Fix the issues in this TargetProcess automation rule.

ORIGINAL RULE:
{refined_rule}

ISSUES TO FIX:
{chr(10).join(f"- {issue}" for issue in issues)}

CONTEXT EXAMPLES:
{self._format_context_for_refinement(context_docs[:5])}

ORIGINAL USER REQUEST: {user_query}

INSTRUCTIONS:
1. Fix each issue listed above
2. Keep the same business logic and functionality
3. Use EXACT patterns from the context examples
4. Ensure all JavaScript syntax is correct
5. Make minimal changes - only fix the specific issues

Return the complete, corrected rule:"""

            try:
                response = self.openai_client.client.chat.completions.create(
                    model=self.openai_client.model_name,
                    messages=[
                        {"role": "system", "content": "You are a rule refinement agent. Fix only the specified issues while preserving functionality."},
                        {"role": "user", "content": refinement_prompt}
                    ],
                    temperature=0.1,
                    max_tokens=2000
                )
                
                refined_rule = response.choices[0].message.content
                logger.info(f"Refinement attempt {attempt + 1} completed")
                
                # Could re-validate here if needed
                break
                
            except Exception as e:
                logger.error(f"Error in refinement attempt {attempt + 1}: {e}")
                if attempt == max_attempts - 1:
                    logger.warning("All refinement attempts failed, returning original rule")
                    return original_rule
        
        logger.info("Rule refinement completed")
        return refined_rule
    
    def _format_context_for_refinement(self, docs: List[Dict]) -> str:
        """Format context docs for refinement"""
        context_parts = []
        for i, doc in enumerate(docs[:3], 1):
            content = doc.get('content', '')[:800]  # Truncate for token limits
            context_parts.append(f"EXAMPLE {i}:\n{content}")
        
        return "\n\n".join(context_parts)

class AgenticRAGOrchestrator:
    """Main orchestrator for agentic RAG system"""
    
    def __init__(self, base_rag_system):
        self.base_rag = base_rag_system
        
        # Initialize agents
        self.planning_agent = QueryPlanningAgent(base_rag_system.openai_client)
        self.retrieval_agent = SpecializedRetrievalAgent(base_rag_system.vector_db)
        self.synthesis_agent = ContextSynthesisAgent(base_rag_system.openai_client)
        self.validation_agent = ValidationAgent(base_rag_system.openai_client)
        self.refinement_agent = RefinementAgent(base_rag_system.openai_client)
        
        logger.info("Agentic RAG Orchestrator initialized with all agents")
    
    def process_complex_query(self, user_query: str, query_type: str = "create_automation", 
                            tp_context: Dict = None, max_results: int = 8) -> Dict[str, Any]:
        """
        Process query using agentic RAG flow
        """
        start_time = datetime.now()
        logger.info(f"Starting agentic RAG processing for query: {user_query[:100]}...")
        
        try:
            # Step 1: Planning
            logger.info("🧠 STEP 1: Query Planning")
            plan = self.planning_agent.plan_query(user_query, tp_context)
            
            # Step 2: Multi-step Retrieval
            logger.info("🔍 STEP 2: Multi-step Retrieval")
            retrieval_results = self.retrieval_agent.multi_step_retrieve(plan, user_query, max_results)
            
            # Step 3: Context Synthesis
            logger.info("🔧 STEP 3: Context Synthesis")
            context_sets = self.synthesis_agent.synthesize_context(retrieval_results, plan, user_query)
            
            # Step 4: Generation (use enhanced context)
            logger.info("⚡ STEP 4: Generation")
            if query_type == "create_automation":
                # Use sample entity data if available
                sample_entity_data = {}
                entity_metadata = None
                
                if plan.get('entity_focus') and self.base_rag.metadata_fetcher:
                    try:
                        entity_type = plan['entity_focus']
                        sample_entity_data = self.base_rag.metadata_fetcher.get_sample_entity_data(entity_type)
                        entity_metadata = self.base_rag.metadata_fetcher.get_entity_metadata(entity_type)
                    except Exception as e:
                        logger.warning(f"Failed to get entity data: {e}")
                
                generated_rule = self.base_rag.openai_client.generate_automation_rule(
                    user_query, 
                    context_sets['primary_context'], 
                    entity_metadata,
                    sample_entity_data,
                    plan.get('complexity', 'medium')
                )
            else:
                # Use base RAG for other query types
                result = self.base_rag.query(user_query, query_type=query_type, max_results=max_results)
                generated_rule = result.get('response', '')
            
            # Step 5: Validation
            logger.info("✅ STEP 5: Validation")
            is_valid, issues, validation_details = self.validation_agent.validate_rule(
                generated_rule, context_sets['primary_context'], plan
            )
            
            # Step 6: Refinement (if needed)
            final_rule = generated_rule
            if not is_valid and issues:
                logger.info("🔄 STEP 6: Refinement")
                final_rule = self.refinement_agent.refine_rule(
                    generated_rule, issues, context_sets['code_examples'], user_query
                )
                
                # Re-validate refined rule
                is_valid, remaining_issues, final_validation = self.validation_agent.validate_rule(
                    final_rule, context_sets['primary_context'], plan
                )
                validation_details['refinement_applied'] = True
                validation_details['remaining_issues'] = len(remaining_issues)
            else:
                validation_details['refinement_applied'] = False
            
            processing_time = (datetime.now() - start_time).total_seconds()
            
            logger.info(f"🎉 Agentic RAG processing complete in {processing_time:.2f}s")
            
            return {
                'success': True,
                'response': final_rule,
                'context_docs': context_sets['primary_context'],
                'metadata': {
                    'processing_mode': 'agentic_rag',
                    'query_plan': plan,
                    'retrieval_categories': list(retrieval_results.keys()),
                    'validation_details': validation_details,
                    'processing_time_seconds': processing_time,
                    'total_docs_retrieved': sum(len(docs) for docs in retrieval_results.values()),
                    'context_synthesis_applied': True,
                    'timestamp': datetime.now().isoformat()
                }
            }
            
        except Exception as e:
            logger.error(f"Error in agentic RAG processing: {e}")
            # Fallback to simple RAG
            logger.info("Falling back to simple RAG")
            return self.base_rag.query(user_query, query_type=query_type, max_results=max_results)