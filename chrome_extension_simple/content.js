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
        this.updateUIForRuleType(); // Initialize UI for default rule type
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
                        <label>Action Type:</label>
                        <div class="tp-radio-group">
                            <label class="tp-radio-label">
                                <input type="radio" name="ruleType" value="create_automation" checked>
                                ⚡ Create Automation Rule
                            </label>
                            <label class="tp-radio-label">
                                <input type="radio" name="ruleType" value="explain_rule">
                                📖 Explain Existing Rule
                            </label>
                            <label class="tp-radio-label">
                                <input type="radio" name="ruleType" value="improve_rule">
                                🔧 Improve Rule
                            </label>
                            <label class="tp-radio-label">
                                <input type="radio" name="ruleType" value="general">
                                💬 General Question
                            </label>
                        </div>
                    </div>
                    
                    <div class="tp-form-group">
                        <label>Complexity Level:</label>
                        <div class="tp-complexity-group">
                            <label class="tp-complexity-label">
                                <input type="radio" name="complexity" value="auto" checked>
                                🤖 Auto-detect
                            </label>
                            <label class="tp-complexity-label">
                                <input type="radio" name="complexity" value="simple">
                                ⚡ Simple (Basic if-then)
                            </label>
                            <label class="tp-complexity-label">
                                <input type="radio" name="complexity" value="medium">
                                🔧 Medium (Some API calls)
                            </label>
                            <label class="tp-complexity-label">
                                <input type="radio" name="complexity" value="complex">
                                🚀 Complex (Full integration)
                            </label>
                        </div>
                    </div>
                    
                    <div class="tp-form-group">
                        <label for="tp-prompt" id="tp-prompt-label">Describe your rule:</label>
                        <textarea 
                            id="tp-prompt" 
                            placeholder="e.g., Create a task when user story is created"
                            rows="4"></textarea>
                        <div id="tp-prompt-help" class="tp-help-text"></div>
                    </div>
                    
                    <div class="tp-form-actions">
                        <button id="tp-generate-btn" class="tp-btn-primary">💡 Generate Rule</button>
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
        const ruleTypeRadios = document.querySelectorAll('input[name="ruleType"]');

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

        // Handle rule type change
        ruleTypeRadios.forEach(radio => {
            radio.addEventListener('change', () => {
                this.updateUIForRuleType();
            });
        });

        // Close panel when clicking outside
        document.addEventListener('click', (e) => {
            if (!this.widget.contains(e.target)) {
                this.hidePanel();
            }
        });
    }

    updateUIForRuleType() {
        const selectedType = document.querySelector('input[name="ruleType"]:checked').value;
        const promptLabel = document.getElementById('tp-prompt-label');
        const promptTextarea = document.getElementById('tp-prompt');
        const promptHelp = document.getElementById('tp-prompt-help');
        const generateBtn = document.getElementById('tp-generate-btn');

        if (selectedType === 'create_automation') {
            promptLabel.textContent = 'Describe the automation rule you want to create:';
            promptTextarea.placeholder = 'e.g., Create a bug when user story is not in Done state';
            promptHelp.textContent = 'Describe what should happen automatically';
            generateBtn.innerHTML = '⚡ Generate Rule';
        } else if (selectedType === 'explain_rule') {
            promptLabel.textContent = 'Paste the rule you want explained:';
            promptTextarea.placeholder = 'Paste your JavaScript automation rule here...';
            promptHelp.textContent = 'Paste the complete rule code for detailed explanation';
            generateBtn.innerHTML = '📖 Explain Rule';
        } else if (selectedType === 'improve_rule') {
            promptLabel.textContent = 'Paste the rule you want to improve:';
            promptTextarea.placeholder = 'Paste your existing rule here for improvement suggestions...';
            promptHelp.textContent = 'Get suggestions to enhance your existing rule';
            generateBtn.innerHTML = '🔧 Improve Rule';
        } else if (selectedType === 'general') {
            promptLabel.textContent = 'Ask any question about automation rules:';
            promptTextarea.placeholder = 'e.g., How do I create a validation rule that prevents editing closed tasks?';
            promptHelp.textContent = 'Ask general questions about TargetProcess automation';
            generateBtn.innerHTML = '💬 Ask Question';
        }
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
        const complexity = document.querySelector('input[name="complexity"]:checked').value;

        if (!prompt) {
            const action = ruleType === 'create_automation' ? 'describe what you want the rule to do' : 'paste the rule you want explained';
            this.showError(`Please ${action}.`);
            return;
        }

        console.log('🚀 Processing request...', { prompt: prompt.substring(0, 100), ruleType });
        this.showLoading(true, ruleType === 'create_automation' ? 'Generating rule...' : 'Explaining rule...');
        this.hideError();
        this.hideResult();

        try {
            // Use different endpoints based on rule type (same as Streamlit logic)
            let endpoint;
            switch(ruleType) {
                case 'create_automation':
                    endpoint = '/generate-rule';
                    break;
                case 'explain_rule':
                    endpoint = '/explain-rule';
                    break;
                case 'improve_rule':
                    endpoint = '/improve-rule';
                    break;
                case 'general':
                    endpoint = '/general-query';
                    break;
                default:
                    endpoint = '/generate-rule';
            }
            
            const response = await fetch(`http://localhost:8000${endpoint}`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    prompt: prompt,
                    rule_type: ruleType,
                    complexity_level: complexity,  // Add complexity parameter
                    entity_type: "UserStory",
                    max_results: 5,      // Same as Streamlit default
                    similarity_threshold: 0.7  // Same as Streamlit default
                })
            });

            if (!response.ok) {
                throw new Error(`Server error: ${response.status}`);
            }

            const result = await response.json();
            console.log('🔍 Full API response:', result);
            console.log('🔍 Response content:', result.response);
            console.log('🔍 Context docs:', result.context_docs?.length || 0);

            if (result.success) {
                if (!result.response || result.response.trim() === '') {
                    console.error('⚠️ Empty response received from server');
                    this.showError('Server returned empty response. Please try again.');
                } else {
                    console.log('✅ Displaying successful result');
                    this.showResult(result, ruleType);
                }
            } else {
                console.error('❌ Server reported failure:', result.error);
                this.showError(result.error || `Failed to ${ruleType === 'create_automation' ? 'generate' : 'explain'} rule`);
            }

        } catch (error) {
            console.error('❌ Error generating rule:', error);
            console.error('Full error details:', {
                message: error.message,
                name: error.name,
                stack: error.stack
            });
            
            // More specific error messages
            let errorMessage = 'Failed to connect to rule generator.';
            if (error.name === 'TypeError' && error.message.includes('fetch')) {
                errorMessage = '🔌 Cannot connect to FastAPI server. Please ensure it is running on localhost:8000';
            } else if (error.message.includes('Server error')) {
                errorMessage = `🔧 Server error: ${error.message}. Check server logs for details.`;
            } else {
                errorMessage = `❌ Error: ${error.message}`;
            }
            
            this.showError(errorMessage);
        } finally {
            this.showLoading(false);
        }
    }

    showResult(result, ruleType) {
        const resultDiv = document.getElementById('tp-result');
        const contentDiv = document.getElementById('tp-result-content');
        const headerTitle = document.querySelector('.tp-result-header h4');
        
        // Update header based on rule type
        headerTitle.textContent = ruleType === 'create_automation' ? 'Generated Rule' : 'Rule Explanation';
        
        // The new API returns a response string (markdown formatted)
        let displayContent = `
            <div class="tp-response-content">
                ${this.formatResponse(result.response)}
            </div>
        `;
        
        // Add context information if available
        if (result.context_docs && result.context_docs.length > 0) {
            displayContent += `
                <div class="tp-context-section">
                    <h5>📚 Source Documents (${result.context_docs.length})</h5>
                    <div class="tp-context-docs">
                        ${result.context_docs.map((doc, i) => `
                            <div class="tp-context-doc">
                                <strong>Document ${i + 1}:</strong> ${doc.metadata?.title || 'Unknown'}<br>
                                <small>Type: ${doc.metadata?.doc_type || 'general'}, Similarity: ${((1 - (doc.distance || 0)) * 100).toFixed(1)}%</small>
                            </div>
                        `).join('')}
                    </div>
                </div>
            `;
        }
        
        // Add metadata if available
        if (result.metadata) {
            displayContent += `
                <div class="tp-metadata-section">
                    <details>
                        <summary>🔍 Query Details</summary>
                        <pre class="tp-metadata">${JSON.stringify(result.metadata, null, 2)}</pre>
                    </details>
                </div>
            `;
        }
        
        contentDiv.innerHTML = displayContent;
        resultDiv.style.display = 'block';
        
        // Set up event listeners for code copy buttons
        this.setupCodeCopyListeners();
    }
    
    formatResponse(response) {
        console.log('Raw response:', response);
        
        if (!response) return '<p>No response received</p>';
        
        // Store original code blocks before processing to preserve formatting
        const codeBlocks = new Map();
        let codeBlockIndex = 0;
        
        // First, extract and store all code blocks with their original formatting
        let tempResponse = response
            .replace(/\*\*JavaScript Code:\*\*\s*```javascript\s*([\s\S]*?)```/gi, (match, code) => {
                const placeholder = `__CODE_BLOCK_${codeBlockIndex}__`;
                codeBlocks.set(placeholder, {
                    code: code,
                    type: 'javascript',
                    title: '💻 JavaScript Code:'
                });
                codeBlockIndex++;
                return placeholder;
            })
            .replace(/```javascript\s*([\s\S]*?)```/gi, (match, code) => {
                const placeholder = `__CODE_BLOCK_${codeBlockIndex}__`;
                codeBlocks.set(placeholder, {
                    code: code,
                    type: 'javascript',
                    title: '💻 JavaScript Code:'
                });
                codeBlockIndex++;
                return placeholder;
            })
            .replace(/```([\s\S]*?)```/g, (match, code) => {
                const placeholder = `__CODE_BLOCK_${codeBlockIndex}__`;
                codeBlocks.set(placeholder, {
                    code: code,
                    type: 'generic',
                    title: '💻 Code:'
                });
                codeBlockIndex++;
                return placeholder;
            });

        // Convert markdown formatting to HTML
        let formatted = tempResponse
            // Then handle inline code
            .replace(/`([^`]+)`/g, '<code>$1</code>')
            // Handle specific formatting patterns from Gemini
            .replace(/\*\*([^\*]+):\*\*/g, '<h5>$1:</h5>')
            .replace(/🔧\s*THEN:/g, '<h4>🔧 THEN:</h4>')
            .replace(/📝\s*DESCRIPTION:/g, '<h4>📝 DESCRIPTION:</h4>')
            // Handle other bold and italic
            .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
            .replace(/\*(.*?)\*/g, '<em>$1</em>')
            // Convert double line breaks to paragraph breaks
            .replace(/\r?\n\r?\n/g, '</p><p>')
            // Convert single line breaks to <br>
            .replace(/\r?\n/g, '<br>');
            
        // Now replace code block placeholders with properly formatted HTML
        codeBlocks.forEach((blockData, placeholder) => {
            const codeId = 'code-' + Math.random().toString(36).substr(2, 9);
            // Store the original code with a data attribute for copying
            const codeHtml = `<div class="tp-code-section">
                <div class="tp-code-header">
                    <h5>${blockData.title}</h5>
                    <button class="tp-code-copy-btn" data-code-id="${codeId}">📋 Copy</button>
                </div>
                <pre class="tp-code" id="${codeId}" data-original-code="${this.encodeForAttribute(blockData.code)}"><code>${this.escapeHtml(blockData.code)}</code></pre>
            </div>`;
            formatted = formatted.replace(placeholder, codeHtml);
        });
        
        // Wrap in paragraph tags if it doesn't start with a tag
        if (!formatted.startsWith('<')) {
            formatted = '<p>' + formatted;
        }
        if (!formatted.endsWith('>')) {
            formatted = formatted + '</p>';
        }
        
        // Clean up empty paragraphs
        formatted = formatted
            .replace(/<p><\/p>/g, '')
            .replace(/<p>\s*<\/p>/g, '')
            .replace(/<p>\s*<br>\s*<\/p>/g, '');
        
        console.log('Formatted response:', formatted);
        return formatted;
    }

    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }

    encodeForAttribute(text) {
        return text
            .replace(/&/g, '&amp;')
            .replace(/"/g, '&quot;')
            .replace(/'/g, '&#39;')
            .replace(/</g, '&lt;')
            .replace(/>/g, '&gt;');
    }

    decodeFromAttribute(text) {
        return text
            .replace(/&quot;/g, '"')
            .replace(/&#39;/g, "'")
            .replace(/&lt;/g, '<')
            .replace(/&gt;/g, '>')
            .replace(/&amp;/g, '&');
    }

    setupCodeCopyListeners() {
        // Remove existing listeners to prevent duplicates
        const existingButtons = document.querySelectorAll('.tp-code-copy-btn');
        existingButtons.forEach(btn => {
            btn.removeEventListener('click', this.handleCodeCopy);
        });

        // Add new listeners
        const copyButtons = document.querySelectorAll('.tp-code-copy-btn');
        copyButtons.forEach(button => {
            button.addEventListener('click', this.handleCodeCopy.bind(this));
        });
    }

    async handleCodeCopy(event) {
        const button = event.target;
        const codeId = button.getAttribute('data-code-id');
        
        if (!codeId) {
            console.error('Code ID not found on button');
            return;
        }

        const codeElement = document.getElementById(codeId);
        if (!codeElement) {
            console.error('Code element not found:', codeId);
            return;
        }
        
        // Try to get the original code from the data attribute first
        let textToCopy = codeElement.getAttribute('data-original-code');
        
        if (textToCopy) {
            // Decode the attribute value to restore original formatting
            textToCopy = this.decodeFromAttribute(textToCopy);
        } else {
            // Fallback to getting text content if data attribute is not available
            const codeContent = codeElement.querySelector('code');
            if (!codeContent) {
                console.error('Code content not found in element:', codeId);
                return;
            }
            textToCopy = codeContent.textContent || codeContent.innerText;
        }
        
        // Clean up any extra whitespace at the beginning and end, but preserve internal formatting
        textToCopy = textToCopy.trim();
        
        console.log('Copying code block with formatting:', textToCopy);
        
        if (textToCopy) {
            try {
                await navigator.clipboard.writeText(textToCopy);
                
                const originalText = button.textContent;
                button.textContent = '✅ Copied!';
                
                setTimeout(() => {
                    button.textContent = originalText;
                }, 2000);
            } catch (error) {
                console.error('Failed to copy code block:', error);
                // Fallback: create a temporary textarea for copying
                this.fallbackCopyCodeBlock(textToCopy, button);
            }
        } else {
            alert('No code content to copy');
        }
    }

    fallbackCopyCodeBlock(text, button) {
        const textarea = document.createElement('textarea');
        textarea.value = text;
        textarea.style.position = 'fixed';
        textarea.style.opacity = '0';
        document.body.appendChild(textarea);
        textarea.select();
        textarea.setSelectionRange(0, 99999);
        
        try {
            document.execCommand('copy');
            const originalText = button.textContent;
            button.textContent = '✅ Copied!';
            
            setTimeout(() => {
                button.textContent = originalText;
            }, 2000);
        } catch (fallbackError) {
            console.error('Fallback copy failed:', fallbackError);
            alert('Copy failed. Please select and copy manually.');
        } finally {
            document.body.removeChild(textarea);
        }
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

    showLoading(show, message = 'Processing...') {
        const loadingDiv = document.getElementById('tp-loading');
        const generateBtn = document.getElementById('tp-generate-btn');
        const loadingText = loadingDiv.querySelector('span');
        const ruleType = document.querySelector('input[name="ruleType"]:checked').value;
        
        loadingDiv.style.display = show ? 'block' : 'none';
        generateBtn.disabled = show;
        
        if (show) {
            if (loadingText) loadingText.textContent = message;
            generateBtn.innerHTML = '⏳ Processing...';
        } else {
            const buttonTexts = {
                'create_automation': '⚡ Generate Rule',
                'explain_rule': '📖 Explain Rule', 
                'improve_rule': '🔧 Improve Rule',
                'general': '💬 Ask Question'
            };
            generateBtn.innerHTML = buttonTexts[ruleType] || '⚡ Generate Rule';
        }
    }

    clearForm() {
        document.getElementById('tp-prompt').value = '';
        this.hideResult();
        this.hideError();
        document.querySelector('input[name="ruleType"][value="automation"]').checked = true;
    }

    async copyResult() {
        // Copy the entire response content
        let textToCopy = '';
        
        const responseElement = document.querySelector('.tp-response-content');
        if (responseElement) {
            textToCopy = responseElement.textContent || responseElement.innerText;
            console.log('Copying full response:', textToCopy);
        }
        
        if (textToCopy && textToCopy.trim()) {
            try {
                await navigator.clipboard.writeText(textToCopy.trim());
                
                const copyBtn = document.getElementById('tp-copy-btn');
                const originalText = copyBtn.textContent;
                copyBtn.textContent = '✅ Copied!';
                
                setTimeout(() => {
                    copyBtn.textContent = originalText;
                }, 2000);
            } catch (error) {
                console.error('Failed to copy:', error);
                // Fallback: create a temporary textarea for copying
                this.fallbackCopy(textToCopy.trim());
            }
        } else {
            alert('No content to copy');
        }
    }
    
    fallbackCopy(text) {
        const textarea = document.createElement('textarea');
        textarea.value = text;
        document.body.appendChild(textarea);
        textarea.select();
        textarea.setSelectionRange(0, 99999);
        
        try {
            document.execCommand('copy');
            const copyBtn = document.getElementById('tp-copy-btn');
            const originalText = copyBtn.textContent;
            copyBtn.textContent = '✅ Copied!';
            
            setTimeout(() => {
                copyBtn.textContent = originalText;
            }, 2000);
        } catch (error) {
            console.error('Fallback copy failed:', error);
            alert('Copy failed. Please select and copy manually.');
        } finally {
            document.body.removeChild(textarea);
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