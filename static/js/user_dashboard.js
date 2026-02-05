// User Dashboard JavaScript - Click Tracking and Session Management with Auto-Refresh

class ClickTracker {
    constructor() {
        this.sessionId = this.generateSessionId();
        this.sessionStart = Date.now();
        this.clickCount = 0;
        this.lastClickTime = null;
        this.ads = [];
        this.refreshInterval = null;
        
        this.init();
    }
    
    generateSessionId() {
        // Include timestamp and random string for uniqueness
        const timestamp = Date.now();
        const random = Math.random().toString(36).substr(2, 9);
        const userSession = this.getUserSessionId(); // Get login session info
        return `session_${timestamp}_${random}_${userSession}`;
    }
    
    getUserSessionId() {
        // Try to get some identifier from login session or create one
        let userSessionId = localStorage.getItem('user_session_id');
        if (!userSessionId) {
            userSessionId = Math.random().toString(36).substr(2, 6);
            localStorage.setItem('user_session_id', userSessionId);
        }
        return userSessionId;
    }
    
    resetSession() {
        // Generate new session ID and reset counters
        localStorage.removeItem('user_session_id'); // Force new user session
        this.sessionId = this.generateSessionId();
        this.sessionStart = Date.now();
        this.clickCount = 0;
        this.lastClickTime = null;
        this.updateSessionDisplay();
    }
    
    init() {
        // Check if this is a fresh page load after login
        const isNewLogin = sessionStorage.getItem('new_login');
        if (isNewLogin) {
            this.resetSession();
            sessionStorage.removeItem('new_login');
        }
        
        this.updateSessionDisplay();
        this.loadAds();
        this.startSessionTimer();
        this.setupModal();
        this.startAutoRefresh();
    }
    
    startAutoRefresh() {
        // Auto-refresh ads every 5 seconds
        this.refreshInterval = setInterval(() => {
            this.loadAds();
        }, 5000);
        console.log('Auto-refresh started: Ads will refresh every 5 seconds');
    }
    
    stopAutoRefresh() {
        if (this.refreshInterval) {
            clearInterval(this.refreshInterval);
            this.refreshInterval = null;
            console.log('Auto-refresh stopped');
        }
    }
    
    updateSessionDisplay() {
        document.getElementById('session-id').textContent = this.sessionId;
        document.getElementById('click-count').textContent = this.clickCount;
        
        const duration = Math.floor((Date.now() - this.sessionStart) / 1000);
        document.getElementById('session-duration').textContent = duration + 's';
        
        if (this.lastClickTime) {
            const gap = ((Date.now() - this.lastClickTime) / 1000).toFixed(1);
            document.getElementById('last-click-gap').textContent = gap + 's';
        }
    }
    
    startSessionTimer() {
        setInterval(() => {
            this.updateSessionDisplay();
        }, 1000);
    }
    
    async loadAds() {
        try {
            const response = await fetch('/ads/active');
            const data = await response.json();
            this.ads = data.ads;
            this.renderAds();
            
            // Update last refresh time
            const now = new Date().toLocaleTimeString();
            let refreshIndicator = document.getElementById('last-refresh');
            if (!refreshIndicator) {
                refreshIndicator = document.createElement('div');
                refreshIndicator.id = 'last-refresh';
                refreshIndicator.style.cssText = `
                    position: fixed;
                    top: 10px;
                    right: 10px;
                    background: rgba(0,0,0,0.7);
                    color: white;
                    padding: 5px 10px;
                    border-radius: 5px;
                    font-size: 12px;
                    z-index: 1000;
                `;
                document.body.appendChild(refreshIndicator);
            }
            refreshIndicator.textContent = `Last refresh: ${now}`;
        } catch (error) {
            console.error('Error loading ads:', error);
            document.getElementById('ads-container').innerHTML = 
                '<div class="error">Failed to load ads. Please refresh the page.</div>';
        }
    }
    
    renderAds() {
        const container = document.getElementById('ads-container');
        
        if (this.ads.length === 0) {
            container.innerHTML = '<div class="no-ads">No ads available</div>';
            return;
        }
        
        container.innerHTML = this.ads.map(ad => `
            <div class="ad-card" data-ad-id="${ad.id}" onclick="clickTracker.handleAdClick(${ad.id})">
                <div class="ad-badge">AD</div>
                <h3>${ad.title}</h3>
                <p>${ad.description}</p>
                <div class="advertiser-name">by ${ad.advertiser_name}</div>
            </div>
        `).join('');
    }
    
    async handleAdClick(adId) {
        const now = Date.now();
        const timeGapSeconds = this.lastClickTime ? (now - this.lastClickTime) / 1000 : 0;
        
        this.clickCount++;
        this.lastClickTime = now;
        
        // Visual feedback
        const adCard = document.querySelector(`[data-ad-id="${adId}"]`);
        adCard.classList.add('clicked');
        
        // Prepare click data
        const clickData = {
            session_id: this.sessionId,
            clicks_per_session: this.clickCount,
            time_gap_seconds: timeGapSeconds,
            session_duration_minutes: (now - this.sessionStart) / (1000 * 60),
            ad_id: adId,
            user_agent_category: this.getUserAgentCategory()
        };
        
        try {
            // Send to fraud detection API
            const response = await fetch('/predict', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(clickData)
            });
            
            if (response.ok) {
                const result = await response.json();
                this.showClickFeedback(result);
            } else {
                this.showClickFeedback(null, 'Error processing click');
            }
        } catch (error) {
            console.error('Error sending click data:', error);
            this.showClickFeedback(null, 'Network error');
        }
        
        this.updateSessionDisplay();
    }
    
    getUserAgentCategory() {
        // Simple user agent categorization for demo
        const ua = navigator.userAgent.toLowerCase();
        
        if (ua.includes('bot') || ua.includes('crawler') || ua.includes('spider')) {
            return 3; // Bot-like
        } else if (ua.includes('mobile') || ua.includes('android') || ua.includes('iphone')) {
            return 2; // Mobile (potentially suspicious if too many rapid clicks)
        } else {
            return 1; // Normal desktop
        }
    }
    
    showClickFeedback(fraudResult, errorMessage = null) {
        const modal = document.getElementById('click-modal');
        const messageEl = document.getElementById('modal-message');
        const fraudInfoEl = document.getElementById('fraud-info');
        
        if (errorMessage) {
            messageEl.textContent = errorMessage;
            fraudInfoEl.style.display = 'none';
        } else if (fraudResult) {
            messageEl.textContent = 'Click recorded successfully.';
            
            // Show fraud analysis (for demo purposes - normally hidden from users)
            document.getElementById('risk-level').textContent = fraudResult.risk_level;
            document.getElementById('fraud-prob').textContent = 
                (fraudResult.fraud_probability * 100).toFixed(1) + '%';
            
            // Only show fraud info if it's high risk (for demo)
            if (fraudResult.risk_level === 'High' || fraudResult.fraud_probability > 0.7) {
                fraudInfoEl.style.display = 'block';
            } else {
                fraudInfoEl.style.display = 'none';
            }
        }
        
        modal.style.display = 'block';
        
        // Auto-close after 3 seconds
        setTimeout(() => {
            modal.style.display = 'none';
        }, 3000);
    }
    
    setupModal() {
        const modal = document.getElementById('click-modal');
        const closeBtn = document.querySelector('.close');
        
        closeBtn.onclick = () => {
            modal.style.display = 'none';
        };
        
        window.onclick = (event) => {
            if (event.target === modal) {
                modal.style.display = 'none';
            }
        };
    }
}

// Bot Simulation Functions (for demo purposes)
class BotSimulator {
    constructor(clickTracker) {
        this.clickTracker = clickTracker;
        this.isRunning = false;
    }
    
    startBotBehavior() {
        if (this.isRunning) return;
        
        this.isRunning = true;
        console.log('🤖 Starting bot-like behavior simulation...');
        
        // Rapid clicks with very short intervals
        const botInterval = setInterval(() => {
            if (!this.isRunning) {
                clearInterval(botInterval);
                return;
            }
            
            const ads = this.clickTracker.ads;
            if (ads.length > 0) {
                const randomAd = ads[Math.floor(Math.random() * ads.length)];
                this.clickTracker.handleAdClick(randomAd.id);
            }
        }, 100 + Math.random() * 200); // Very fast clicks (100-300ms)
        
        // Stop after 10 seconds
        setTimeout(() => {
            this.stopBotBehavior();
        }, 10000);
    }
    
    stopBotBehavior() {
        this.isRunning = false;
        console.log('🛑 Bot behavior simulation stopped');
    }
}

// Initialize when page loads
let clickTracker;
let botSimulator;

document.addEventListener('DOMContentLoaded', () => {
    clickTracker = new ClickTracker();
    botSimulator = new BotSimulator(clickTracker);
    
    // Add bot simulation button (for demo)
    const sessionInfo = document.querySelector('.session-info');
    const botButton = document.createElement('button');
    botButton.textContent = '🤖 Simulate Bot Clicks (Demo)';
    botButton.style.cssText = `
        background: #e74c3c;
        color: white;
        border: none;
        padding: 0.5rem 1rem;
        border-radius: 5px;
        cursor: pointer;
        margin-top: 1rem;
    `;
    botButton.onclick = () => botSimulator.startBotBehavior();
    sessionInfo.appendChild(botButton);
});

// Keyboard shortcuts for demo
document.addEventListener('keydown', (e) => {
    if (e.ctrlKey && e.key === 'b') {
        e.preventDefault();
        botSimulator.startBotBehavior();
    }
});