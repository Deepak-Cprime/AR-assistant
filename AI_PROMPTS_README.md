# AI Prompt System - Detailed Analysis

This document explains the sophisticated prompt engineering system used in the AR/VR Helper application for generating TargetProcess automation rules through AI.

## Prompt Architecture Overview

The system employs **multi-modal prompt engineering** with four distinct prompt types, each optimized for specific user intents and complexity levels.

## 1. Rule Generation Prompt (`generate_automation_rule`)

**Purpose**: Create new TargetProcess automation rules from natural language descriptions

**Key Features**:
- **Context-Aware Prompting**: Integrates live TargetProcess metadata and sample entity data
- **Structured Output Format**: Forces consistent rule structure with visual formatting
- **Complexity Adaptation**: Adjusts generation parameters based on rule complexity (simple/medium/complex)
- **Syntax Enforcement**: Strict validation of JavaScript syntax and TargetProcess API patterns

**Prompt Components**:

### System Context
```
You are an expert in Targetprocess automation rules. Your task is to create a working automation rule with a STRUCTURED, CONCISE format for a Chrome extension floating widget.
```

### Dynamic Metadata Injection
```
LIVE TARGETPROCESS METADATA (Use these exact field names and values):
-- Entity Type: {entity_metadata.get('entity_type', 'Unknown')}
-- Available Standard Fields: {', '.join(entity_metadata.get('standard_fields', []))}
```

### Real-World Example Integration
```
REAL EXAMPLE FROM YOUR TARGETPROCESS INSTANCE:
Entity: {sample_data.get('Name', 'Sample')} (ID: {sample_data.get('Id', 'N/A')})
```

### Critical Syntax Enforcement
- **JSON Safety**: Prevents template literal usage in JSON payloads
- **String Concatenation**: Enforces proper JavaScript string concatenation patterns
- **API Compliance**: Ensures TargetProcess-specific API call structure

**Advanced Techniques Used**:
- **Few-shot Learning**: Uses retrieved documentation examples
- **Chain-of-thought**: Step-by-step rule construction guidance
- **Constraint-based Generation**: Strict formatting and syntax rules
- **Domain-specific Validation**: TargetProcess entity and field validation

## 2. Rule Explanation Prompt (`explain_existing_rule`)

**Purpose**: Provide comprehensive explanations of existing automation rules

**Analytical Framework**:
1. **Functionality Analysis**: What the rule does
2. **Trigger Analysis**: When it executes
3. **Condition Analysis**: What filters are applied
4. **Action Analysis**: What operations are performed
5. **Use Case Analysis**: Business value and applications
6. **Risk Analysis**: Limitations and considerations

**Prompt Strategy**:
- **Documentation Grounding**: References provided context documents
- **Multi-perspective Explanation**: Technical and business perspectives
- **Structured Analysis**: Consistent 6-point analysis framework
- **Accessibility Focus**: Clear language for both technical and non-technical users

## 3. Rule Improvement Prompt (`suggest_improvements`)

**Purpose**: Analyze and enhance existing automation rules

**Enhancement Categories**:
1. **Performance Optimization**: Efficiency improvements
2. **Error Handling**: Robustness enhancements
3. **Filtering Enhancement**: Better condition logic
4. **Functionality Extension**: Additional capabilities
5. **Best Practices**: Industry standard compliance
6. **Code Modernization**: Updated configurations

**Advanced Analysis Techniques**:
- **Pattern Recognition**: Identifies common anti-patterns
- **Performance Profiling**: Suggests optimization strategies
- **Security Analysis**: Identifies potential vulnerabilities
- **Maintainability Assessment**: Code quality improvements

## 4. General Question Answering Prompt (`answer_question`)

**Purpose**: Respond to general queries about TargetProcess and automation rules

**Knowledge Grounding Strategy**:
- **Strict Documentation Adherence**: Only uses provided context
- **Source Attribution**: References specific documents
- **Exact Syntax Preservation**: Maintains original code patterns
- **Multi-step Guidance**: Provides structured how-to instructions

**Response Structure**:
1. **Direct Answer**: Immediate response to query
2. **Working Example**: Code/configuration from documentation
3. **Step-by-Step Guide**: Implementation instructions
4. **Related Information**: Contextual knowledge
5. **Source References**: Document citations

## Prompt Engineering Techniques

### 1. **Dynamic Context Injection**
- Real-time TargetProcess metadata integration
- Live entity field validation
- Sample data enrichment
- API response formatting

### 2. **Constraint-Based Generation**
```javascript
// Enforced patterns:
✅ CORRECT: Name: "User Story " + args.Current.Id + " exceeds deadline"
❌ WRONG: Name: `User Story ${args.Current.Id} exceeds deadline`
```

### 3. **Multi-Level Complexity Adaptation**
- **Simple**: Basic if-then logic, low temperature (0.2)
- **Medium**: Moderate API usage, balanced parameters (0.3)
- **Complex**: Full integration, higher creativity (0.4)

### 4. **Structured Output Enforcement**
```
RULE CONFIGURATION:
═══════════════════════════════════════════════════════════════════
📋 RULE NAME: [Descriptive name]
🎯 WHEN: [Trigger conditions]
🔧 THEN: [Actions to perform]
📝 DESCRIPTION: [Purpose explanation]
```

### 5. **Error Prevention Strategies**
- **Syntax Validation**: Prevents common JavaScript errors
- **API Compliance**: Ensures TargetProcess compatibility
- **JSON Safety**: Avoids template literal issues
- **Null Handling**: Proper error boundary implementation

### 6. **Documentation Grounding**
- **Example Matching**: Aligns with provided documentation patterns
- **API Consistency**: Uses documented function signatures
- **Pattern Replication**: Maintains established coding style
- **Best Practice Integration**: Incorporates documentation recommendations

## Complexity Detection Algorithm

The system auto-detects complexity using keyword analysis:

**Simple Indicators**: create, when, if, simple, basic
**Complex Indicators**: api, multiple, complex, advanced, integrate, fetch, query

This drives:
- **Temperature Adjustment**: More deterministic for simple rules
- **Token Limits**: Appropriate response length
- **Context Depth**: Relevant documentation selection

## Quality Assurance Features

1. **Syntax Validation**: Pre-execution code validation
2. **API Compliance**: TargetProcess API conformance
3. **Error Boundary**: Graceful failure handling
4. **Output Sanitization**: Safe code generation
5. **Documentation Alignment**: Consistency with examples

This prompt system demonstrates advanced NLP techniques including few-shot learning, constraint-based generation, dynamic context injection, and multi-modal reasoning for reliable automation rule generation.