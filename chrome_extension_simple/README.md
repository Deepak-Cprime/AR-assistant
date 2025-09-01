# Chrome Extension - TargetProcess Rule Generator

This Chrome extension provides a floating widget interface for generating automation and validation rules directly within TargetProcess pages.

## Technical Implementation

### Core Architecture

**Manifest V3 Service Worker Pattern**
- Uses modern Chrome Extension Manifest V3 with service worker background script
- Implements proper async/await patterns for better performance and reliability
- Employs event-driven architecture for efficient resource management

**Content Script Injection**
- Dynamic content script injection on TargetProcess domains only
- URL pattern matching with wildcard support for multiple TargetProcess instances
- DOM-ready initialization with fallback loading strategies

### Key Components & Techniques

#### 1. Widget System (`content.js`)
- **Class-based Widget Architecture**: Encapsulated `RuleGeneratorWidget` class with proper lifecycle management
- **Dynamic DOM Manipulation**: Runtime creation of floating UI elements with event delegation
- **State Management**: Internal state tracking for widget visibility and form data
- **Event-driven Interactions**: Comprehensive event listener setup with proper cleanup

#### 2. Background Service Worker (`background.js`)
- **Chrome Extension APIs**: Leverages `chrome.runtime`, `chrome.tabs`, `chrome.action`, and `chrome.notifications`
- **Tab Lifecycle Management**: Monitors tab updates and removes for badge management
- **Message Passing**: Bidirectional communication between background, content, and popup scripts
- **Health Monitoring**: API server status checking with connection validation

#### 3. UI/UX Features
- **Floating Button Interface**: CSS-based positioning with z-index management
- **Modal Panel System**: Toggle-based show/hide with click-outside dismissal
- **Form State Management**: Radio button groups with dynamic UI updates
- **Loading States**: Visual feedback with spinner animations and button state management

#### 4. Advanced Functionality
- **Multi-mode Operation**: Support for rule creation, explanation, improvement, and general queries
- **Complexity Level Selection**: User-configurable complexity settings for AI responses
- **Response Formatting**: Markdown-to-HTML conversion with code syntax highlighting
- **Code Block Management**: Individual copy buttons with clipboard API integration and fallback methods

### API Integration Techniques

**RESTful Communication**
- Fetch API with proper error handling and timeout management
- JSON-based request/response patterns
- Dynamic endpoint selection based on rule type

**Error Handling Patterns**
- Comprehensive try-catch blocks with specific error categorization
- User-friendly error messaging with technical details for debugging
- Fallback mechanisms for clipboard operations and API failures

### Browser Compatibility Features

**Modern Web APIs**
- Clipboard API with fallback to legacy `document.execCommand`
- CSS Grid and Flexbox for responsive layout
- ES6+ features with proper browser compatibility

**Cross-domain Communication**
- Content Security Policy compliance
- Host permissions for TargetProcess domains
- Secure message passing between isolated contexts

### Performance Optimizations

- **Lazy Loading**: Widget creation only when needed
- **Event Delegation**: Efficient event handling with minimal memory footprint  
- **DOM Caching**: Strategic element caching to reduce DOM queries
- **Debounced Operations**: Prevents rapid successive API calls

## Code Examples

### Widget Initialization & DOM Manipulation
```javascript
// content.js - Advanced widget creation with context awareness
class RuleGeneratorWidget {
    createWidget() {
        // Dynamic widget creation with event delegation
        this.widget = document.createElement('div');
        this.widget.id = 'tp-rule-generator';
        this.widget.innerHTML = this.generateWidgetHTML();
        
        // Strategic DOM insertion with fallback
        const targetContainer = document.body;
        targetContainer.appendChild(this.widget);
        
        // Apply dynamic styles with CSS injection
        this.injectCustomStyles();
        
        // Context-aware initialization
        this.detectTargetProcessContext();
    }
    
    detectTargetProcessContext() {
        // Extract TargetProcess entity context from current page
        const url = window.location.href;
        const entityMatches = {
            userstory: /\/UserStory\/(\d+)/,
            bug: /\/Bug\/(\d+)/, 
            feature: /\/Feature\/(\d+)/,
            task: /\/Task\/(\d+)/
        };
        
        for (const [entityType, pattern] of Object.entries(entityMatches)) {
            const match = url.match(pattern);
            if (match) {
                this.currentContext = {
                    entityType,
                    entityId: match[1],
                    pageUrl: url
                };
                this.updateUIForContext(entityType);
                break;
            }
        }
    }
}
```

### Service Worker Architecture
```javascript
// background.js - Advanced Chrome API integration
class TargetProcessExtensionManager {
    constructor() {
        this.apiServerUrl = 'http://localhost:8000';
        this.healthCheckInterval = null;
        this.setupEventListeners();
    }
    
    async checkApiServerStatus() {
        // Health check with timeout and retry logic
        const timeout = 5000;
        const controller = new AbortController();
        const timeoutId = setTimeout(() => controller.abort(), timeout);
        
        try {
            const response = await fetch(`${this.apiServerUrl}/health`, {
                signal: controller.signal,
                method: 'GET',
                cache: 'no-cache'
            });
            
            clearTimeout(timeoutId);
            
            if (response.ok) {
                const status = await response.json();
                this.updateBadgeStatus('online', '✓');
                return { online: true, ...status };
            } else {
                throw new Error(`Server returned ${response.status}`);
            }
        } catch (error) {
            clearTimeout(timeoutId);
            this.updateBadgeStatus('offline', '⚠');
            throw error;
        }
    }
    
    updateBadgeStatus(status, text) {
        // Dynamic badge management with visual feedback
        chrome.action.setBadgeText({ text });
        chrome.action.setBadgeBackgroundColor({
            color: status === 'online' ? '#4CAF50' : '#FF5722'
        });
        
        chrome.action.setTitle({
            title: `TargetProcess Rule Generator - API Server ${status}`
        });
    }
}
```

### API Integration with Retry Logic
```javascript
// content.js - Robust API communication patterns
class ApiClient {
    constructor(baseUrl = 'http://localhost:8000') {
        this.baseUrl = baseUrl;
        this.defaultTimeout = 30000;
        this.maxRetries = 3;
    }
    
    async makeRequest(endpoint, data, options = {}) {
        const { timeout = this.defaultTimeout, retries = this.maxRetries } = options;
        
        for (let attempt = 1; attempt <= retries; attempt++) {
            try {
                // AbortController for timeout management
                const controller = new AbortController();
                const timeoutId = setTimeout(() => controller.abort(), timeout);
                
                const response = await fetch(`${this.baseUrl}${endpoint}`, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'X-Request-Attempt': attempt.toString(),
                        'X-Client-Version': chrome.runtime.getManifest().version
                    },
                    body: JSON.stringify(data),
                    signal: controller.signal
                });
                
                clearTimeout(timeoutId);
                
                if (!response.ok) {
                    throw new Error(`HTTP ${response.status}: ${response.statusText}`);
                }
                
                return await response.json();
                
            } catch (error) {
                console.warn(`API attempt ${attempt}/${retries} failed:`, error.message);
                
                if (attempt === retries) {
                    throw new Error(`API request failed after ${retries} attempts: ${error.message}`);
                }
                
                // Exponential backoff with jitter
                const backoffTime = Math.pow(2, attempt) * 1000 + Math.random() * 1000;
                await new Promise(resolve => setTimeout(resolve, backoffTime));
            }
        }
    }
    
    async generateRule(query, complexity, ruleType) {
        // Context-enriched API call
        const requestData = {
            query,
            complexity,
            context: {
                page_url: window.location.href,
                entity_type: this.extractEntityType(),
                project_context: this.getProjectContext(),
                user_preferences: this.getUserPreferences()
            }
        };
        
        const endpoint = this.getEndpointForRuleType(ruleType);
        return await this.makeRequest(endpoint, requestData);
    }
}
```

### Advanced UI State Management
```javascript
// content.js - Sophisticated state management
class WidgetStateManager {
    constructor() {
        this.state = {
            isVisible: false,
            isLoading: false,
            currentMode: 'create_automation',
            complexity: 'medium',
            lastQuery: '',
            history: []
        };
        
        this.subscribers = new Set();
        this.stateProxy = new Proxy(this.state, {
            set: (target, property, value) => {
                const oldValue = target[property];
                target[property] = value;
                
                if (oldValue !== value) {
                    this.notifySubscribers(property, value, oldValue);
                }
                
                return true;
            }
        });
    }
    
    subscribe(callback) {
        this.subscribers.add(callback);
        return () => this.subscribers.delete(callback);
    }
    
    notifySubscribers(property, newValue, oldValue) {
        this.subscribers.forEach(callback => {
            try {
                callback({ property, newValue, oldValue, state: this.state });
            } catch (error) {
                console.error('State subscriber error:', error);
            }
        });
    }
    
    updateUI(stateChange) {
        const { property, newValue } = stateChange;
        
        switch (property) {
            case 'isLoading':
                this.toggleLoadingUI(newValue);
                break;
            case 'currentMode':
                this.updateModeUI(newValue);
                break;
            case 'complexity':
                this.updateComplexityIndicator(newValue);
                break;
        }
    }
}
```

### Performance Optimizations & Memory Management
```javascript
// content.js - Resource management patterns
class ResourceManager {
    constructor() {
        this.observers = new Map();
        this.timers = new Set();
        this.eventListeners = new Map();
    }
    
    createMutationObserver(target, callback, options) {
        // Efficient DOM observation with cleanup
        const observer = new MutationObserver(callback);
        observer.observe(target, options);
        
        this.observers.set(target, observer);
        return observer;
    }
    
    addEventListenerWithCleanup(element, event, handler, options = {}) {
        // Event listener management with automatic cleanup
        element.addEventListener(event, handler, options);
        
        const key = `${element.tagName}-${event}`;
        if (!this.eventListeners.has(key)) {
            this.eventListeners.set(key, []);
        }
        this.eventListeners.get(key).push({ element, event, handler, options });
    }
    
    cleanup() {
        // Comprehensive resource cleanup
        this.observers.forEach(observer => observer.disconnect());
        this.observers.clear();
        
        this.timers.forEach(timerId => clearTimeout(timerId));
        this.timers.clear();
        
        this.eventListeners.forEach(listeners => {
            listeners.forEach(({ element, event, handler }) => {
                element.removeEventListener(event, handler);
            });
        });
        this.eventListeners.clear();
    }
}
```

This extension demonstrates advanced Chrome Extension development patterns, modern JavaScript techniques, and robust error handling while maintaining a clean, user-friendly interface.