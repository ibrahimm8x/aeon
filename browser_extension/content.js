// AEON Web Activity Tracker - Content Script
// Tracks page views, clicks, and other user interactions

class AEONActivityTracker {
    constructor() {
        this.userId = null;
        this.sessionId = null;
        this.pageStartTime = Date.now();
        this.aeonServerUrl = 'http://localhost:8000';
        this.isTracking = false;
        
        this.init();
    }
    
    async init() {
        // Get user configuration from storage
        const config = await this.getConfig();
        if (config && config.userId) {
            this.userId = config.userId;
            this.sessionId = config.sessionId;
            this.isTracking = true;
            
            // Start tracking
            this.startTracking();
        }
    }
    
    async getConfig() {
        return new Promise((resolve) => {
            chrome.storage.local.get(['aeonUserId', 'aeonSessionId'], (result) => {
                resolve({
                    userId: result.aeonUserId,
                    sessionId: result.aeonSessionId
                });
            });
        });
    }
    
    startTracking() {
        if (!this.isTracking) return;
        
        // Track page view
        this.trackPageView();
        
        // Track clicks
        this.trackClicks();
        
        // Track form submissions
        this.trackFormSubmissions();
        
        // Track search queries
        this.trackSearchQueries();
        
        // Track page visibility changes
        this.trackPageVisibility();
        
        // Track scroll depth
        this.trackScrollDepth();
        
        // Send page view data when page is about to unload
        window.addEventListener('beforeunload', () => {
            this.trackPageView(true); // Final page view
        });
    }
    
    trackPageView(isFinal = false) {
        const pageData = {
            type: 'page_view',
            url: window.location.href,
            title: document.title,
            referrer: document.referrer,
            user_agent: navigator.userAgent,
            duration: isFinal ? Date.now() - this.pageStartTime : null,
            timestamp: new Date().toISOString()
        };
        
        this.sendActivityData(pageData);
    }
    
    trackClicks() {
        document.addEventListener('click', (event) => {
            const target = event.target;
            const clickData = {
                type: 'click',
                url: window.location.href,
                element_type: target.tagName.toLowerCase(),
                element_text: target.textContent?.trim().substring(0, 100) || null,
                element_id: target.id || null,
                element_class: target.className || null,
                timestamp: new Date().toISOString()
            };
            
            this.sendActivityData(clickData);
        });
    }
    
    trackFormSubmissions() {
        document.addEventListener('submit', (event) => {
            const form = event.target;
            const formData = {
                type: 'form_submit',
                url: window.location.href,
                form_id: form.id || null,
                form_action: form.action || null,
                form_method: form.method || null,
                timestamp: new Date().toISOString()
            };
            
            this.sendActivityData(formData);
        });
    }
    
    trackSearchQueries() {
        // Monitor search engines
        const searchEngines = {
            'google.com': 'q',
            'bing.com': 'q',
            'yahoo.com': 'p',
            'duckduckgo.com': 'q',
            'youtube.com': 'search_query'
        };
        
        const currentDomain = window.location.hostname;
        const searchParam = searchEngines[currentDomain];
        
        if (searchParam) {
            const urlParams = new URLSearchParams(window.location.search);
            const query = urlParams.get(searchParam);
            
            if (query) {
                const searchData = {
                    type: 'search',
                    query: query,
                    engine: currentDomain,
                    url: window.location.href,
                    timestamp: new Date().toISOString()
                };
                
                this.sendActivityData(searchData);
            }
        }
    }
    
    trackPageVisibility() {
        let hidden = false;
        let visibilityChange = null;
        
        if (typeof document.hidden !== "undefined") {
            hidden = "hidden";
            visibilityChange = "visibilitychange";
        } else if (typeof document.msHidden !== "undefined") {
            hidden = "msHidden";
            visibilityChange = "msvisibilitychange";
        } else if (typeof document.webkitHidden !== "undefined") {
            hidden = "webkitHidden";
            visibilityChange = "webkitvisibilitychange";
        }
        
        if (visibilityChange) {
            document.addEventListener(visibilityChange, () => {
                const visibilityData = {
                    type: 'visibility_change',
                    url: window.location.href,
                    is_hidden: document[hidden],
                    timestamp: new Date().toISOString()
                };
                
                this.sendActivityData(visibilityData);
            });
        }
    }
    
    trackScrollDepth() {
        let maxScrollDepth = 0;
        
        window.addEventListener('scroll', () => {
            const scrollTop = window.pageYOffset || document.documentElement.scrollTop;
            const scrollHeight = document.documentElement.scrollHeight - window.innerHeight;
            const scrollDepth = Math.round((scrollTop / scrollHeight) * 100);
            
            if (scrollDepth > maxScrollDepth) {
                maxScrollDepth = scrollDepth;
                
                // Send scroll data every 25% of scroll depth
                if (scrollDepth % 25 === 0) {
                    const scrollData = {
                        type: 'scroll_depth',
                        url: window.location.href,
                        scroll_depth: scrollDepth,
                        timestamp: new Date().toISOString()
                    };
                    
                    this.sendActivityData(scrollData);
                }
            }
        });
    }
    
    async sendActivityData(activityData) {
        if (!this.userId || !this.isTracking) return;
        
        try {
            const payload = {
                user_id: this.userId,
                session_id: this.sessionId,
                data: activityData
            };
            
            // Send to AEON server via WebSocket or HTTP
            await this.sendToAEON(payload);
            
        } catch (error) {
            console.error('Error sending activity data:', error);
        }
    }
    
    async sendToAEON(payload) {
        // Try WebSocket first, fallback to HTTP
        if (this.websocket && this.websocket.readyState === WebSocket.OPEN) {
            this.websocket.send(JSON.stringify({
                type: 'web_activity',
                data: payload
            }));
        } else {
            // Fallback to HTTP
            await fetch(`${this.aeonServerUrl}/api/v1/aeon/web-activity`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(payload)
            });
        }
    }
    
    connectWebSocket() {
        try {
            this.websocket = new WebSocket(`ws://localhost:8000/api/v1/phase3/ws/${this.userId}`);
            
            this.websocket.onopen = () => {
                console.log('AEON WebSocket connected');
            };
            
            this.websocket.onmessage = (event) => {
                const message = JSON.parse(event.data);
                this.handleWebSocketMessage(message);
            };
            
            this.websocket.onerror = (error) => {
                console.error('AEON WebSocket error:', error);
            };
            
            this.websocket.onclose = () => {
                console.log('AEON WebSocket disconnected');
                // Try to reconnect after 5 seconds
                setTimeout(() => this.connectWebSocket(), 5000);
            };
            
        } catch (error) {
            console.error('Error connecting to AEON WebSocket:', error);
        }
    }
    
    handleWebSocketMessage(message) {
        switch (message.type) {
            case 'activity_tracked':
                console.log('Activity tracked successfully');
                break;
            case 'productivity_reminder':
                this.showProductivityReminder(message.data);
                break;
            case 'activity_insights':
                this.showActivityInsights(message.data);
                break;
            default:
                console.log('Received message:', message);
        }
    }
    
    showProductivityReminder(data) {
        // Create a notification
        const notification = document.createElement('div');
        notification.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            background: #ff6b6b;
            color: white;
            padding: 15px;
            border-radius: 8px;
            box-shadow: 0 4px 12px rgba(0,0,0,0.15);
            z-index: 10000;
            max-width: 300px;
            font-family: Arial, sans-serif;
        `;
        
        notification.innerHTML = `
            <h4>AEON Productivity Reminder</h4>
            <p>${data.message}</p>
            <p>Productivity Score: ${data.productivity_score}%</p>
            <button onclick="this.parentElement.remove()" style="background: white; border: none; padding: 5px 10px; border-radius: 4px; cursor: pointer;">Dismiss</button>
        `;
        
        document.body.appendChild(notification);
        
        // Auto-remove after 10 seconds
        setTimeout(() => {
            if (notification.parentElement) {
                notification.remove();
            }
        }, 10000);
    }
    
    showActivityInsights(data) {
        // Create insights notification
        const notification = document.createElement('div');
        notification.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            background: #4ecdc4;
            color: white;
            padding: 15px;
            border-radius: 8px;
            box-shadow: 0 4px 12px rgba(0,0,0,0.15);
            z-index: 10000;
            max-width: 300px;
            font-family: Arial, sans-serif;
        `;
        
        const topTopics = Object.entries(data.top_topics)
            .sort(([,a], [,b]) => b - a)
            .slice(0, 3)
            .map(([topic, count]) => `${topic} (${count})`)
            .join(', ');
        
        notification.innerHTML = `
            <h4>AEON Activity Insights</h4>
            <p>You've visited ${data.total_activities} pages today</p>
            <p>Top topics: ${topTopics}</p>
            <p>Productivity: ${data.productivity_score}%</p>
            <button onclick="this.parentElement.remove()" style="background: white; border: none; padding: 5px 10px; border-radius: 4px; cursor: pointer;">Dismiss</button>
        `;
        
        document.body.appendChild(notification);
        
        // Auto-remove after 15 seconds
        setTimeout(() => {
            if (notification.parentElement) {
                notification.remove();
            }
        }, 15000);
    }
}

// Initialize the tracker when the page loads
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
        new AEONActivityTracker();
    });
} else {
    new AEONActivityTracker();
} 