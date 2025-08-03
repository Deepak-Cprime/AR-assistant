"""
FastAPI server for TargetProcess automation and validation rules
Simple, focused API for generating rules based on user prompts
"""
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, Dict, Any
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="TargetProcess Rule Generator API",
    description="Generate automation and validation rules for TargetProcess",
    version="1.0.0"
)

# Enable CORS for Chrome extension
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Request models
class RuleRequest(BaseModel):
    prompt: str
    rule_type: str  # "automation" or "validation"
    entity_type: Optional[str] = "UserStory"

class RuleResponse(BaseModel):
    success: bool
    rule_name: str
    entity: str
    trigger: str
    field: str
    condition: str
    value: str
    javascript_code: str
    description: str
    error: Optional[str] = None

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "TargetProcess Rule Generator API",
        "version": "1.0.0",
        "endpoints": {
            "health": "/health",
            "generate_rule": "/generate-rule"
        }
    }

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "TargetProcess Rule Generator"
    }

@app.post("/generate-rule", response_model=RuleResponse)
async def generate_rule(request: RuleRequest):
    """
    Generate automation or validation rule based on user prompt
    """
    try:
        logger.info(f"Generating {request.rule_type} rule for: {request.prompt}")
        
        # Parse the prompt to understand the intent
        prompt_lower = request.prompt.lower()
        
        # Determine rule components based on prompt analysis
        rule_components = analyze_prompt(request.prompt, request.rule_type, request.entity_type)
        
        # Generate the appropriate rule
        if request.rule_type == "automation":
            rule = generate_automation_rule(rule_components)
        elif request.rule_type == "validation":
            rule = generate_validation_rule(rule_components)
        else:
            raise HTTPException(status_code=400, detail="Invalid rule_type. Must be 'automation' or 'validation'")
        
        return RuleResponse(**rule)
        
    except Exception as e:
        logger.error(f"Error generating rule: {e}")
        raise HTTPException(status_code=500, detail=str(e))

def analyze_prompt(prompt: str, rule_type: str, entity_type: str) -> Dict[str, Any]:
    """
    Analyze user prompt to extract rule components
    """
    prompt_lower = prompt.lower()
    
    # Extract entities
    entities = {
        'user story': 'UserStory', 'story': 'UserStory', 'userstory': 'UserStory',
        'bug': 'Bug', 'bugs': 'Bug', 'defect': 'Bug',
        'task': 'Task', 'tasks': 'Task',
        'feature': 'Feature', 'features': 'Feature',
        'epic': 'Epic', 'epics': 'Epic'
    }
    
    detected_entity = entity_type
    for keyword, entity in entities.items():
        if keyword in prompt_lower:
            detected_entity = entity
            break
    
    # Extract actions/triggers
    triggers = {
        'create': 'Created', 'add': 'Created', 'new': 'Created',
        'update': 'Updated', 'change': 'Updated', 'modify': 'Updated',
        'move': 'Updated', 'assign': 'Updated', 'set': 'Updated',
        'delete': 'Deleted', 'remove': 'Deleted'
    }
    
    detected_trigger = 'Updated'  # Default
    for keyword, trigger in triggers.items():
        if keyword in prompt_lower:
            detected_trigger = trigger
            break
    
    # Extract fields
    fields = {
        'state': 'State', 'status': 'State',
        'owner': 'Owner', 'assign': 'Owner', 'user': 'Owner',
        'priority': 'Priority',
        'effort': 'Effort', 'estimate': 'Effort',
        'project': 'Project',
        'team': 'Team'
    }
    
    detected_field = 'State'  # Default
    for keyword, field in fields.items():
        if keyword in prompt_lower:
            detected_field = field
            break
    
    # Extract conditions/values
    conditions = []
    if 'block' in prompt_lower:
        conditions.append({'field': 'State', 'value': 'Blocked'})
    if 'done' in prompt_lower or 'complete' in prompt_lower:
        conditions.append({'field': 'State', 'value': 'Done'})
    if 'progress' in prompt_lower:
        conditions.append({'field': 'State', 'value': 'In Progress'})
    if 'high' in prompt_lower and 'priority' in prompt_lower:
        conditions.append({'field': 'Priority', 'value': 'High'})
    
    return {
        'prompt': prompt,
        'entity': detected_entity,
        'trigger': detected_trigger,
        'field': detected_field,
        'conditions': conditions if conditions else [{'field': detected_field, 'value': 'any change'}],
        'rule_type': rule_type
    }

def generate_automation_rule(components: Dict[str, Any]) -> Dict[str, Any]:
    """
    Generate automation rule based on analyzed components
    """
    entity = components['entity']
    trigger = components['trigger']
    field = components['field']
    conditions = components['conditions']
    prompt = components['prompt']
    
    # Generate rule name
    rule_name = f"Auto-action when {entity} {field.lower()} changes"
    
    # Generate JavaScript code based on the prompt
    if 'bug' in prompt.lower() and 'block' in prompt.lower():
        # Create bug when something is blocked
        javascript_code = f'''const utils = require("utils");

if (args.ChangedFields.contains("{field}") && args.Current.{field}.Name === "{conditions[0]['value']}") {{
    return utils.createResource("Bug", {{
        Name: `Issue: ${{args.Current.Name}} is blocked`,
        Description: `Automatically created because ${{args.ResourceType}} "${{args.Current.Name}}" was moved to {conditions[0]['value']} state.`,
        Project: {{ Id: args.Current.Project.Id }},
        {entity}: {{ Id: args.ResourceId }},
        Priority: {{ Name: "High" }},
        Owner: args.Current.Owner
    }});
}}'''
    elif 'task' in prompt.lower() and 'create' in prompt.lower():
        # Create task for user story
        javascript_code = f'''const utils = require("utils");

if (args.Modification === "Created" || (args.ChangedFields.contains("{field}") && args.Current.{field}.Name === "{conditions[0]['value']}")) {{
    return utils.createResource("Task", {{
        Name: `Implementation: ${{args.Current.Name}}`,
        Description: `Auto-created task for ${{args.ResourceType.toLowerCase()}} implementation`,
        Project: {{ Id: args.Current.Project.Id }},
        {entity}: {{ Id: args.ResourceId }},
        Owner: args.Current.Owner,
        EntityState: {{ Name: "To Do" }}
    }});
}}'''
    elif 'assign' in prompt.lower():
        # Auto-assign based on criteria
        javascript_code = f'''const utils = require("utils");

if (args.ChangedFields.contains("{field}")) {{
    let assigneeId = null;
    
    // Assignment logic based on conditions
    if (args.Current.{field} && args.Current.{field}.Name === "{conditions[0]['value']}") {{
        // Assign to project manager or team lead
        assigneeId = args.Current.Project.Owner ? args.Current.Project.Owner.Id : null;
    }}
    
    if (assigneeId && (!args.Current.Owner || args.Current.Owner.Id !== assigneeId)) {{
        return utils.updateResource(args.ResourceType, args.ResourceId, {{
            Owner: {{ Id: assigneeId }}
        }});
    }}
}}'''
    else:
        # Generic automation rule
        javascript_code = f'''const utils = require("utils");

if (args.ChangedFields.contains("{field}")) {{
    const currentValue = args.Current.{field} ? args.Current.{field}.Name : null;
    const previousValue = args.Previous && args.Previous.{field} ? args.Previous.{field}.Name : null;
    
    if (currentValue === "{conditions[0]['value']}" && currentValue !== previousValue) {{
        // Perform your automation action here
        console.log(`${{args.ResourceType}} ${{args.Current.Name}} {field.lower()} changed to ${{currentValue}}`);
        
        // Example: Update another field or create related entity
        return utils.updateResource(args.ResourceType, args.ResourceId, {{
            // Add your field updates here
            // Example: CustomField: "Automated Update"
        }});
    }}
}}'''
    
    return {
        "success": True,
        "rule_name": rule_name,
        "entity": entity,
        "trigger": trigger,
        "field": field,
        "condition": "equals" if conditions[0]['value'] != 'any change' else "changed",
        "value": conditions[0]['value'],
        "javascript_code": javascript_code,
        "description": f"Automatically performs actions when {entity} {field} meets specified conditions based on: {prompt}"
    }

def generate_validation_rule(components: Dict[str, Any]) -> Dict[str, Any]:
    """
    Generate validation rule based on analyzed components
    """
    entity = components['entity']
    field = components['field']
    conditions = components['conditions']
    prompt = components['prompt']
    
    rule_name = f"Validate {entity} {field.lower()} requirements"
    
    # Generate validation JavaScript code
    if 'require' in prompt.lower() or 'must' in prompt.lower():
        javascript_code = f'''// Validation rule based on: {prompt}

if (args.Modification === "Created" || args.ChangedFields.contains("{field}")) {{
    const errors = [];
    
    // Validation logic based on your requirements
    if (!args.Current.{field} || args.Current.{field}.Name === "") {{
        errors.push("{field} is required");
    }}
    
    if (args.Current.{field} && args.Current.{field}.Name === "{conditions[0]['value']}" && !args.Current.Owner) {{
        errors.push("Items in {conditions[0]['value']} state must have an assigned owner");
    }}
    
    if (args.Current.Priority && args.Current.Priority.Name === "Critical" && !args.Current.Owner) {{
        errors.push("Critical items must be assigned to someone");
    }}
    
    // Return validation errors if any
    if (errors.length > 0) {{
        return {{
            success: false,
            errors: errors
        }};
    }}
    
    return {{ success: true }};
}}'''
    else:
        # Generic validation rule
        javascript_code = f'''// Validation rule for {entity} {field}

if (args.Modification === "Created" || args.Modification === "Updated") {{
    const errors = [];
    
    // Basic validation rules
    if (!args.Current.Name || args.Current.Name.trim() === "") {{
        errors.push("Name is required");
    }}
    
    if (args.Current.Name && args.Current.Name.length < 5) {{
        errors.push("Name must be at least 5 characters");
    }}
    
    if (args.Current.{field} && args.Current.{field}.Name === "{conditions[0]['value']}") {{
        // Add specific validation for this condition
        if (!args.Current.Description || args.Current.Description.trim() === "") {{
            errors.push("Description is required when {field} is {conditions[0]['value']}");
        }}
    }}
    
    // Return validation result
    if (errors.length > 0) {{
        return {{
            success: false,
            errors: errors
        }};
    }}
    
    return {{ success: true }};
}}'''
    
    return {
        "success": True,
        "rule_name": rule_name,
        "entity": entity,
        "trigger": "Created/Updated",
        "field": field,
        "condition": "validation check",
        "value": conditions[0]['value'],
        "javascript_code": javascript_code,
        "description": f"Validates {entity} data to ensure: {prompt}"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)