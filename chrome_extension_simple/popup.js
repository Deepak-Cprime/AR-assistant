/**
 * Popup script for TargetProcess Rule Generator Chrome extension
 * Handles extension popup interactions and status checks
 */

document.addEventListener('DOMContentLoaded', function() {
    const openTpBtn = document.getElementById('open-tp');
    const checkApiBtn = document.getElementById('check-api');
    const helpBtn = document.getElementById('help');
    const statusElement = document.getElementById('status');

    // Check if we're on a TargetProcess page
    checkCurrentTab();

    // Event listeners
    openTpBtn.addEventListener('click', openTargetProcess);
    checkApiBtn.addEventListener('click', checkApiServer);
    helpBtn.addEventListener('click', showHelp);

    async function checkCurrentTab() {
        try {
            const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
            
            if (tab && isTargetProcessPage(tab.url)) {
                updateStatus(true, 'Active on TargetProcess page');
            } else {
                updateStatus(false, 'Navigate to TargetProcess to use');
            }
        } catch (error) {
            console.error('Error checking current tab:', error);
            updateStatus(false, 'Unable to detect page status');
        }
    }

    function isTargetProcessPage(url) {
        if (!url) return false;
        return url.includes('targetprocess.com') || 
               url.includes('tp-devops.com') || 
               url.includes('tpondemand.com');
    }

    function updateStatus(isActive, message) {
        const indicator = statusElement.querySelector('.status-indicator');
        const text = statusElement.querySelector('span:last-child');
        
        if (isActive) {
            indicator.className = 'status-indicator status-active';
            text.textContent = message;
        } else {
            indicator.className = 'status-indicator status-inactive';
            text.textContent = message;
        }
    }

    async function openTargetProcess() {
        try {
            // Try to find existing TargetProcess tab
            const tabs = await chrome.tabs.query({});
            const tpTab = tabs.find(tab => isTargetProcessPage(tab.url));
            
            if (tpTab) {
                // Switch to existing TargetProcess tab
                await chrome.tabs.update(tpTab.id, { active: true });
                await chrome.windows.update(tpTab.windowId, { focused: true });
            } else {
                // Open new TargetProcess tab
                await chrome.tabs.create({ 
                    url: 'https://www.targetprocess.com/',
                    active: true
                });
            }
            
            // Close popup
            window.close();
        } catch (error) {
            console.error('Error opening TargetProcess:', error);
            alert('Unable to open TargetProcess. Please try manually.');
        }
    }

    async function checkApiServer() {
        const originalText = checkApiBtn.textContent;
        checkApiBtn.textContent = 'Checking...';
        checkApiBtn.disabled = true;

        try {
            const response = await fetch('http://localhost:8000/health', {
                method: 'GET',
                headers: {
                    'Content-Type': 'application/json',
                }
            });

            if (response.ok) {
                const data = await response.json();
                alert(`✅ API Server is running!\n\nStatus: ${data.status}\nService: ${data.service}`);
            } else {
                throw new Error(`Server responded with status: ${response.status}`);
            }
        } catch (error) {
            console.error('API check failed:', error);
            alert(`❌ API Server is not running!\n\nError: ${error.message}\n\nMake sure to start the FastAPI server:\n1. Open terminal in fastapi_server folder\n2. Run: pip install -r requirements.txt\n3. Run: python main.py`);
        } finally {
            checkApiBtn.textContent = originalText;
            checkApiBtn.disabled = false;
        }
    }

    function showHelp() {
        const helpMessage = `🤖 TargetProcess Rule Generator Help

📍 How to Use:
1. Navigate to any TargetProcess page
2. Look for the floating "🤖 Rules" button (bottom-right)
3. Click it to open the rule generator
4. Select rule type (Automation or Validation)
5. Describe what you want the rule to do
6. Click "Generate Rule" to get JavaScript code

⚙️ Setup Requirements:
• FastAPI server running on localhost:8000
• TargetProcess access
• Chrome extension permissions

🔧 Troubleshooting:
• If the floating button doesn't appear, refresh the page
• If rule generation fails, check API server status
• Make sure you're on a TargetProcess page

💡 Example Prompts:
• "Create a bug when user story is blocked"
• "Require owner when priority is high"
• "Auto-assign tasks to project owner"
• "Validate description is required"

🚀 Version 1.0.0`;

        alert(helpMessage);
    }
});