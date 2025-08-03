# TargetProcess API Integration Setup

This guide explains how to configure the AR/VR Helper to use live data from your TargetProcess instance for generating precise automation rules.

## 🎯 Overview

The enhanced system now:
- **Uses RAG Knowledge Base**: 150+ documents with automation rule examples
- **Calls Live TargetProcess API**: Gets real field names, states, and entity structures
- **Provides Precise Rules**: Uses actual data from your TP instance

## 🔧 Setup Steps

### 1. Get TargetProcess API Token

1. **Log into your TargetProcess instance**
2. **Go to Settings** → Access Tokens
3. **Create New Token**:
   - Name: `AR_VR_Helper`
   - Permissions: `Read` (minimum required)
   - Expiration: Set as needed
4. **Copy the token** - you'll need it for configuration

### 2. Configure Environment Variables

Create or update your `.env` file:

```env
# Gemini AI Configuration
GEMINI_API_KEY=your_gemini_api_key_here

# TargetProcess Configuration
TARGETPROCESS_DOMAIN=your-company.targetprocess.com
TARGETPROCESS_TOKEN=your_access_token_here
```

**Important**: 
- Use your actual TP domain (without `https://`)
- Keep the access token secure and private

### 3. Verify Configuration

Run the API server and test:

```bash
# Start the API server
python api_server.py

# Test the connection (from another terminal)
python -c "
from src.metadata_fetcher import TargetprocessMetadata
import os
from dotenv import load_dotenv

load_dotenv()
domain = os.getenv('TARGETPROCESS_DOMAIN')
token = os.getenv('TARGETPROCESS_TOKEN')

if domain and token:
    tp = TargetprocessMetadata(domain, token)
    if tp.test_connection():
        print('✅ TargetProcess connection successful')
        # Test entity metadata
        metadata = tp.get_entity_metadata('UserStory')
        print(f'📊 Found {len(metadata[\"standard_fields\"])} fields, {len(metadata[\"states\"])} states')
    else:
        print('❌ TargetProcess connection failed')
else:
    print('⚠️ TargetProcess credentials not configured')
"
```

## 🌟 Enhanced Features

### Precise Field Names
Instead of generic field suggestions, the system now uses your actual TP fields:
```javascript
// Before: Generic suggestions
args.Current.SomeField

// After: Your actual fields
args.Current.PlannedEndDate
args.Current["Custom Risk Level"]
args.Current.EntityState.Name
```

### Real State Names
Uses your actual workflow states:
```javascript
// Your actual states from TP
EntityState.Name == "In Development"
EntityState.Name == "Ready for Testing" 
EntityState.Name == "Customer Review"
```

### Custom Field Support
Handles your custom fields correctly:
```javascript
// Proper access patterns for custom fields
args.Current["Risk Level"]
args.Current["Business Priority"]
args.Current.CustomField.Value
```

## 🔍 How It Works

### 1. Query Processing
```
User Query → RAG Search → Live TP API → Enhanced Context → Precise Rule
```

### 2. Live Data Integration
- **Entity Metadata**: Real field names and types
- **State Information**: Actual workflow states
- **Custom Fields**: Your organization's custom fields
- **Relationships**: Proper entity relationships

### 3. Context Enrichment
The Chrome extension can pass additional context:
```javascript
{
  "url": "https://company.targetprocess.com/entity/userstory/123",
  "entityType": "UserStory",
  "currentState": "In Progress",
  "projectName": "Mobile App"
}
```

## 📊 Example Output

**Query**: "Create a rule that creates a risk when planned end date exceeded"

**Before** (Generic):
```json
{
  "name": "Risk Alert Rule",
  "actions": [{
    "type": "CreateEntity",
    "entityType": "Risk"
  }]
}
```

**After** (With Live TP Data):
```json
{
  "name": "Risk Alert for User Story Past Planned End Date",
  "triggerType": "EntityChanged",
  "sources": [{
    "type": "source:targetprocess:EntityChanged",
    "entityTypes": ["UserStory"],
    "modifications": ["Updated"]
  }],
  "actions": [{
    "type": "action:JavaScript",
    "script": "const api = context.getService('targetprocess/api/v2');\nif (args.Current.PlannedEndDate && new Date(args.Current.PlannedEndDate) < new Date()) {\n  return {\n    command: 'targetprocess:CreateResource',\n    payload: {\n      resourceType: 'Risk',\n      fields: {\n        Name: 'Overdue: ' + args.Current.Name,\n        EntityState: { Name: 'Open' },\n        UserStory: { Id: args.ResourceId }\n      }\n    }\n  };\n}"
  }]
}
```

## 🛡️ Security Notes

1. **API Token Permissions**: Use minimal required permissions (Read-only)
2. **Environment Variables**: Never commit `.env` file to version control
3. **Token Rotation**: Regularly rotate your API tokens
4. **Network Security**: Ensure HTTPS connections to TP API

## 🔧 Troubleshooting

### Connection Issues
```bash
# Test basic connectivity
curl "https://your-domain.targetprocess.com/api/v1/Context?access_token=your_token"
```

### Permission Issues
- Ensure token has access to read entities
- Check if your user account has necessary permissions
- Verify the token hasn't expired

### Field Access Issues
- Some fields may be restricted based on user permissions
- Custom fields need proper configuration in TP
- Check field names are case-sensitive

## 📈 Performance Notes

- **Caching**: Entity metadata is cached for performance
- **Rate Limiting**: API calls are managed to avoid rate limits
- **Fallback**: System falls back to generic patterns if API fails

---

**Ready to create precise automation rules with live TargetProcess data!** 🚀