/**
 * Background service worker for TargetProcess Rule Generator Chrome extension
 * Handles extension lifecycle and provides utility functions
 */

// Extension installation and startup
chrome.runtime.onInstalled.addListener((details) => {
    console.log('TargetProcess Rule Generator extension installed:', details.reason);
    
    if (details.reason === 'install') {
        // Show welcome notification on first install
        chrome.notifications?.create('welcome', {
            type: 'basic',
            iconUrl: 'icon.png',
            title: '🤖 Rule Generator Installed!',
            message: 'Navigate to TargetProcess and look for the floating Rules button.'
        });
    } else if (details.reason === 'update') {
        console.log('Extension updated to version:', chrome.runtime.getManifest().version);
    }
});

// Handle extension startup
chrome.runtime.onStartup.addListener(() => {
    console.log('TargetProcess Rule Generator extension started');
});

// Handle messages from content scripts or popup
chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
    console.log('Background received message:', request);
    
    switch (request.action) {
        case 'checkApiServer':
            checkApiServerStatus()
                .then(status => sendResponse({ success: true, status }))
                .catch(error => sendResponse({ success: false, error: error.message }));
            return true; // Keep message channel open for async response
            
        case 'logError':
            console.error('Content script error:', request.error);
            sendResponse({ received: true });
            break;
            
        case 'logInfo':
            console.log('Content script info:', request.message);
            sendResponse({ received: true });
            break;
            
        default:
            console.warn('Unknown message action:', request.action);
            sendResponse({ success: false, error: 'Unknown action' });
    }
});

// Check API server status
async function checkApiServerStatus() {
    try {
        const response = await fetch('http://localhost:8000/health', {
            method: 'GET',
            headers: {
                'Content-Type': 'application/json',
            }
        });
        
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}`);
        }
        
        const data = await response.json();
        return {
            online: true,
            status: data.status,
            service: data.service
        };
    } catch (error) {
        return {
            online: false,
            error: error.message
        };
    }
}

// Handle tab updates to inject content script on TargetProcess pages
chrome.tabs.onUpdated.addListener((tabId, changeInfo, tab) => {
    // Only act when the tab is completely loaded
    if (changeInfo.status === 'complete' && tab.url) {
        const isTargetProcessPage = 
            tab.url.includes('targetprocess.com') ||
            tab.url.includes('tp-devops.com') ||
            tab.url.includes('tpondemand.com');
            
        if (isTargetProcessPage) {
            console.log('TargetProcess page detected:', tab.url);
            
            // Set badge to indicate extension is active
            chrome.action.setBadgeText({
                text: '●',
                tabId: tabId
            });
            
            chrome.action.setBadgeBackgroundColor({
                color: '#667eea',
                tabId: tabId
            });
        } else {
            // Clear badge for non-TargetProcess pages
            chrome.action.setBadgeText({
                text: '',
                tabId: tabId
            });
        }
    }
});

// Handle tab removal to clean up any stored data
chrome.tabs.onRemoved.addListener((tabId) => {
    console.log('Tab removed:', tabId);
    // Clean up any tab-specific storage if needed
});

// Utility function to get active tab
async function getActiveTab() {
    try {
        const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
        return tab;
    } catch (error) {
        console.error('Error getting active tab:', error);
        return null;
    }
}

// Utility function to check if URL is a TargetProcess page
function isTargetProcessPage(url) {
    if (!url) return false;
    return url.includes('targetprocess.com') || 
           url.includes('tp-devops.com') || 
           url.includes('tpondemand.com');
}

// Handle extension icon click (when popup is not available)
chrome.action.onClicked.addListener(async (tab) => {
    if (isTargetProcessPage(tab.url)) {
        // Send message to content script to show/hide panel
        try {
            await chrome.tabs.sendMessage(tab.id, { action: 'togglePanel' });
        } catch (error) {
            console.error('Error sending message to content script:', error);
        }
    } else {
        // Show notification that extension only works on TargetProcess pages
        chrome.notifications?.create('not-tp-page', {
            type: 'basic',
            iconUrl: 'icon.png',
            title: '🤖 Rule Generator',
            message: 'This extension only works on TargetProcess pages. Navigate to your TargetProcess instance first.'
        });
    }
});

// Clean up notifications
chrome.notifications?.onClicked.addListener((notificationId) => {
    chrome.notifications.clear(notificationId);
});

chrome.notifications?.onClosed.addListener((notificationId) => {
    console.log('Notification closed:', notificationId);
});

// Log extension info
console.log('TargetProcess Rule Generator background script loaded');
console.log('Extension version:', chrome.runtime.getManifest().version);