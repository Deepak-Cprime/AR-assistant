/**
 * Content script for TargetProcess Rule Generator
 * Creates a floating button on TargetProcess pages
 */

class RuleGeneratorWidget {
    constructor() {
        this.isVisible = false;
        this.widget = null;
        this.init();
    }

    init() {
        console.log('TargetProcess Rule Generator: Initializing...');
        console.log('Current URL:', window.location.href);
        console.log('Hostname:', window.location.hostname);
        
        // For testing: Show on all pages, but log if it's a TargetProcess page
        const isTPPage = this.isTargetProcessPage();
        if (isTPPage) {
            console.log('TargetProcess page detected!');
        } else {
            console.log('Not a TargetProcess page, but loading widget for testing');
        }
        
        console.log('TargetProcess page detected, loading widget...');
        this.createWidget();
        this.setupEventListeners();
        console.log('TargetProcess Rule Generator widget loaded successfully');
    }

    isTargetProcessPage() {
        const hostname = window.location.hostname;
        const url = window.location.href;
        
        // Check for TargetProcess domains
        const isTPDomain = hostname.includes('targetprocess.com') || 
                          hostname.includes('tp-devops.com') || 
                          hostname.includes('tpondemand.com');
        
        // For testing: also allow localhost or any page with 'targetprocess' in URL
        const isTestPage = hostname.includes('localhost') || 
                          url.toLowerCase().includes('targetprocess');
        
        console.log('TargetProcess check:', { hostname, url, isTPDomain, isTestPage });
        
        return isTPDomain || isTestPage;
    }

    createWidget() {
        // Create floating button
        this.widget = document.createElement('div');
        this.widget.id = 'tp-rule-generator';
        this.widget.innerHTML = `
            <div class="tp-floating-btn" id="tp-floating-btn">
                <span class="tp-btn-text">🤖 Rules</span>
            </div>
            
            <div class="tp-panel" id="tp-panel" style="display: none;">
                <div class="tp-panel-header">
                    <h3>🤖 Rule Generator</h3>
                    <button class="tp-close-btn" id="tp-close-btn">×</button>
                </div>
                
                <div class="tp-panel-content">
                    <div class="tp-form-group">
                        <label>Rule Type:</label>
                        <div class="tp-radio-group">
                            <label class="tp-radio-label">
                                <input type="radio" name="ruleType" value="automation" checked>
                                ⚡ Automation
                            </label>
                            <label class="tp-radio-label">
                                <input type="radio" name="ruleType" value="validation">
                                ✅ Validation
                            </label>
                        </div>
                    </div>
                    
                    <div class="tp-form-group">
                        <label for="tp-prompt">Describe your rule:</label>
                        <textarea 
                            id="tp-prompt" 
                            placeholder="e.g., Create a bug when user story is blocked"
                            rows="3"></textarea>
                    </div>
                    
                    <div class="tp-form-actions">
                        <button id="tp-generate-btn" class="tp-btn-primary">Generate Rule</button>
                        <button id="tp-clear-btn" class="tp-btn-secondary">Clear</button>
                    </div>
                    
                    <div id="tp-loading" class="tp-loading" style="display: none;">
                        <div class="tp-spinner"></div>
                        <span>Generating rule...</span>
                    </div>
                    
                    <div id="tp-result" class="tp-result" style="display: none;">
                        <div class="tp-result-header">
                            <h4>Generated Rule</h4>
                            <button id="tp-copy-btn" class="tp-copy-btn">📋 Copy</button>
                        </div>
                        <div id="tp-result-content" class="tp-result-content"></div>
                    </div>
                    
                    <div id="tp-error" class="tp-error" style="display: none;"></div>
                </div>
            </div>
        `;

        document.body.appendChild(this.widget);
    }

    setupEventListeners() {
        const floatingBtn = document.getElementById('tp-floating-btn');
        const panel = document.getElementById('tp-panel');
        const closeBtn = document.getElementById('tp-close-btn');
        const generateBtn = document.getElementById('tp-generate-btn');
        const clearBtn = document.getElementById('tp-clear-btn');
        const copyBtn = document.getElementById('tp-copy-btn');

        // Toggle panel
        floatingBtn.addEventListener('click', () => {
            this.togglePanel();
        });

        // Close panel
        closeBtn.addEventListener('click', () => {
            this.hidePanel();
        });

        // Generate rule
        generateBtn.addEventListener('click', () => {
            this.generateRule();
        });

        // Clear form
        clearBtn.addEventListener('click', () => {
            this.clearForm();
        });

        // Copy result
        copyBtn.addEventListener('click', () => {
            this.copyResult();
        });

        // Close panel when clicking outside
        document.addEventListener('click', (e) => {
            if (!this.widget.contains(e.target)) {
                this.hidePanel();
            }
        });
    }

    togglePanel() {
        const panel = document.getElementById('tp-panel');
        if (panel.style.display === 'none') {
            this.showPanel();
        } else {
            this.hidePanel();
        }
    }

    showPanel() {
        const panel = document.getElementById('tp-panel');
        panel.style.display = 'block';
        this.isVisible = true;
    }

    hidePanel() {
        const panel = document.getElementById('tp-panel');
        panel.style.display = 'none';
        this.isVisible = false;
    }

    async generateRule() {
        const prompt = document.getElementById('tp-prompt').value.trim();
        const ruleType = document.querySelector('input[name="ruleType"]:checked').value;

        if (!prompt) {
            this.showError('Please describe what you want the rule to do.');
            return;
        }

        this.showLoading(true);
        this.hideError();
        this.hideResult();

        try {
            const response = await fetch('http://localhost:8000/generate-rule', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    prompt: prompt,
                    rule_type: ruleType,
                    entity_type: "UserStory"
                })
            });

            if (!response.ok) {
                throw new Error(`Server error: ${response.status}`);
            }

            const result = await response.json();

            if (result.success) {
                this.showResult(result);
            } else {
                this.showError(result.error || 'Failed to generate rule');
            }

        } catch (error) {
            console.error('Error generating rule:', error);
            this.showError('Failed to connect to rule generator. Make sure the FastAPI server is running on localhost:8000');
        } finally {
            this.showLoading(false);
        }
    }

    showResult(rule) {
        const resultDiv = document.getElementById('tp-result');
        const contentDiv = document.getElementById('tp-result-content');
        
        contentDiv.innerHTML = `
            <div class="tp-rule-summary">
                <h5>📋 ${rule.rule_name}</h5>
                <div class="tp-rule-details">
                    <div><strong>Entity:</strong> ${rule.entity}</div>
                    <div><strong>Trigger:</strong> ${rule.trigger}</div>
                    <div><strong>Field:</strong> ${rule.field}</div>
                    <div><strong>Condition:</strong> ${rule.condition}</div>
                    <div><strong>Value:</strong> ${rule.value}</div>
                </div>
            </div>
            
            <div class="tp-code-section">
                <h5>JavaScript Code:</h5>
                <pre class="tp-code"><code>${rule.javascript_code}</code></pre>
            </div>
            
            <div class="tp-description">
                <p>${rule.description}</p>
            </div>
        `;
        
        resultDiv.style.display = 'block';
    }

    showError(message) {
        const errorDiv = document.getElementById('tp-error');
        errorDiv.textContent = message;
        errorDiv.style.display = 'block';
    }

    hideError() {
        const errorDiv = document.getElementById('tp-error');
        errorDiv.style.display = 'none';
    }

    hideResult() {
        const resultDiv = document.getElementById('tp-result');
        resultDiv.style.display = 'none';
    }

    showLoading(show) {
        const loadingDiv = document.getElementById('tp-loading');
        const generateBtn = document.getElementById('tp-generate-btn');
        
        loadingDiv.style.display = show ? 'block' : 'none';
        generateBtn.disabled = show;
        generateBtn.textContent = show ? 'Generating...' : 'Generate Rule';
    }

    clearForm() {
        document.getElementById('tp-prompt').value = '';
        this.hideResult();
        this.hideError();
        document.querySelector('input[name="ruleType"][value="automation"]').checked = true;
    }

    async copyResult() {
        const codeElement = document.querySelector('.tp-code code');
        if (codeElement) {
            try {
                await navigator.clipboard.writeText(codeElement.textContent);
                
                const copyBtn = document.getElementById('tp-copy-btn');
                const originalText = copyBtn.textContent;
                copyBtn.textContent = '✅ Copied!';
                
                setTimeout(() => {
                    copyBtn.textContent = originalText;
                }, 2000);
            } catch (error) {
                console.error('Failed to copy:', error);
            }
        }
    }
}

// Initialize the widget when the page loads
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
        new RuleGeneratorWidget();
    });
} else {
    new RuleGeneratorWidget();
}