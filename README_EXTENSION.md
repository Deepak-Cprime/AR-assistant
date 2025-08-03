# TargetProcess Rule Generator Extension

A Chrome extension that generates automation and validation rules for TargetProcess using a simple floating interface.

## 🚀 Quick Start

### 1. Start the FastAPI Server

```bash
cd fastapi_server
pip install fastapi uvicorn
python main.py
```

The server will start on `http://localhost:8000`

### 2. Install Chrome Extension

1. Open Chrome and go to `chrome://extensions/`
2. Enable "Developer mode" (top right toggle)
3. Click "Load unpacked"
4. Select the `chrome_extension_simple` folder
5. The extension should now appear in your extensions

### 3. Use the Extension

1. Navigate to any TargetProcess page (e.g., `https://yourcompany.targetprocess.com`)
2. Look for the floating "🤖 Rules" button in the bottom-right corner
3. Click the button to open the rule generator
4. Select rule type (Automation or Validation)
5. Describe what you want the rule to do
6. Click "Generate Rule" to get JavaScript code
7. Copy the generated code and paste it into TargetProcess Rule Editor

## 📁 Project Structure

```
AR_VR_helper/
├── fastapi_server/          # FastAPI backend server
│   ├── main.py             # Main API server with rule generation logic
│   └── requirements.txt    # Python dependencies
├── chrome_extension_simple/ # Chrome extension files
│   ├── manifest.json       # Extension configuration
│   ├── content.js          # Floating widget implementation
│   ├── styles.css          # Extension styling
│   ├── popup.html          # Extension popup interface
│   ├── popup.js            # Popup functionality
│   └── background.js       # Background service worker
└── README_EXTENSION.md     # This file
```

## 🎯 Features

### ✨ Smart Rule Generation
- Analyzes natural language prompts
- Generates proper TargetProcess JavaScript syntax
- Supports both automation and validation rules
- Provides rule summaries with entity, trigger, and conditions

### 🎪 Floating Interface
- Non-intrusive floating button
- Clean, modern interface
- Works only on TargetProcess pages
- Easy copy-to-clipboard functionality

### 🔧 API Integration
- RESTful FastAPI backend
- Real-time rule generation
- Error handling and status checking
- CORS support for Chrome extension

## 📝 Example Prompts

### Automation Rules
- "Create a bug when user story is blocked"
- "Auto-assign tasks to project owner"
- "Create task when user story is done"
- "Update priority when state changes"

### Validation Rules
- "Require owner when priority is high"
- "Validate description is required"
- "Check effort is set for user stories"
- "Ensure name is at least 5 characters"

## 🛠️ API Endpoints

### Health Check
```bash
GET http://localhost:8000/health
```

### Generate Rule
```bash
POST http://localhost:8000/generate-rule
Content-Type: application/json

{
  "prompt": "Create a bug when user story is blocked",
  "rule_type": "automation",
  "entity_type": "UserStory"
}
```

## 🔍 Troubleshooting

### Extension Not Working
1. Make sure you're on a TargetProcess page
2. Check if the API server is running (`http://localhost:8000/health`)
3. Refresh the page to reload the content script
4. Check browser console for errors

### API Server Issues
1. Ensure Python and pip are installed
2. Install dependencies: `pip install fastapi uvicorn`
3. Check if port 8000 is available
4. Look at server logs for error messages

### Rule Generation Fails
1. Verify API server is running
2. Check network connectivity
3. Try simpler prompts
4. Check browser console for CORS errors

## 📊 Technical Details

### Chrome Extension
- **Manifest Version**: 3
- **Permissions**: storage, activeTab
- **Host Permissions**: TargetProcess domains + localhost:8000
- **Content Script**: Injects floating widget on TargetProcess pages

### FastAPI Server
- **Framework**: FastAPI with CORS middleware
- **Port**: 8000
- **Response Format**: JSON with rule details and JavaScript code
- **Prompt Analysis**: Keyword-based entity and trigger detection

### Rule Generation Logic
- Analyzes user prompts for entities (UserStory, Bug, Task)
- Detects triggers (Created, Updated, Deleted)
- Identifies fields (State, Owner, Priority)
- Generates appropriate JavaScript code templates
- Returns structured rule information

## 🎉 Usage Tips

1. **Be Specific**: More detailed prompts generate better rules
2. **Use Keywords**: Mention entities like "user story", "bug", "task"
3. **State Actions**: Use verbs like "create", "update", "assign"
4. **Test Rules**: Always test generated rules in a safe environment first
5. **Iterate**: Try different phrasings if the first result isn't perfect

## 🔄 Version History

- **v1.0.0**: Initial release with floating extension and FastAPI backend