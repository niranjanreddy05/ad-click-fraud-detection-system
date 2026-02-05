// Advertiser Dashboard JavaScript with Authentication and Auto-Refresh

class AdvertiserDashboard {
    constructor() {
        this.currentAdvertiser = null;
        this.autoRefreshInterval = null;
        this.isAutoRefresh = true; // Start with auto-refresh enabled
        this.currentTab = 'analytics';
        this.refreshIntervals = {
            analytics: null,
            ads: null
        };
        
        this.init();
    }
    
    async init() {
        try {
            // Check authentication
            await this.checkAuth();
            
            // Setup event listeners
            this.setupEventListeners();
            
            // Load initial data
            this.switchTab('analytics');
        } catch (error) {
            console.error('Authentication failed:', error);
            window.location.href = '/login';
        }
    }
    
    async checkAuth() {
        try {
            const response = await fetch('/auth/me');
            if (!response.ok) {
                throw new Error('Not authenticated');
            }
            
            this.currentAdvertiser = await response.json();
            document.getElementById('advertiser-name').textContent = this.currentAdvertiser.name;
        } catch (error) {
            throw error;
        }
    }
    
    setupEventListeners() {
        // Tab navigation
        document.querySelectorAll('.tab-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                const tab = e.target.dataset.tab;
                this.switchTab(tab);
            });
        });
        
        // Logout button
        document.getElementById('logout-btn').addEventListener('click', () => {
            this.logout();
        });
        
        // Analytics tab controls
        document.getElementById('refresh-btn')?.addEventListener('click', () => {
            this.refreshAnalytics();
        });
        
        document.getElementById('auto-refresh-btn')?.addEventListener('click', () => {
            this.toggleAutoRefresh();
        });
        
        // Ads tab controls
        document.getElementById('refresh-ads-btn')?.addEventListener('click', () => {
            this.loadMyAds();
        });
        
        // Create ad form
        document.getElementById('create-ad-form')?.addEventListener('submit', (e) => {
            e.preventDefault();
            this.createAd();
        });
    }
    
    switchTab(tabName) {
        // Update tab buttons
        document.querySelectorAll('.tab-btn').forEach(btn => {
            btn.classList.remove('active');
            if (btn.dataset.tab === tabName) {
                btn.classList.add('active');
            }
        });
        
        // Update tab content
        document.querySelectorAll('.tab-content').forEach(content => {
            content.classList.remove('active');
        });
        
        const activeTab = document.getElementById(`${tabName}-tab`);
        if (activeTab) {
            activeTab.classList.add('active');
        }
        
        // Stop previous tab's auto-refresh
        this.stopTabRefresh(this.currentTab);
        
        this.currentTab = tabName;
        
        // Load tab-specific data and start auto-refresh
        switch (tabName) {
            case 'analytics':
                this.refreshAnalytics();
                this.startTabRefresh('analytics');
                break;
            case 'ads':
                this.loadMyAds();
                this.startTabRefresh('ads');
                break;
            case 'create-ad':
                // No auto-refresh needed for create form
                break;
        }
    }
    
    startTabRefresh(tabName) {
        // Clear any existing interval for this tab
        this.stopTabRefresh(tabName);
        
        // Start new interval based on tab
        switch (tabName) {
            case 'analytics':
                this.refreshIntervals.analytics = setInterval(() => {
                    if (this.currentTab === 'analytics') {
                        this.refreshAnalytics();
                    }
                }, 5000);
                break;
            case 'ads':
                this.refreshIntervals.ads = setInterval(() => {
                    if (this.currentTab === 'ads') {
                        this.loadMyAds();
                    }
                }, 5000);
                break;
        }
        
        // Update refresh indicator
        this.updateRefreshIndicator(tabName);
    }
    
    stopTabRefresh(tabName) {
        if (this.refreshIntervals[tabName]) {
            clearInterval(this.refreshIntervals[tabName]);
            this.refreshIntervals[tabName] = null;
        }
    }
    
    updateRefreshIndicator(tabName) {
        const now = new Date().toLocaleTimeString();
        let refreshIndicator = document.getElementById('refresh-indicator');
        if (!refreshIndicator) {
            refreshIndicator = document.createElement('div');
            refreshIndicator.id = 'refresh-indicator';
            refreshIndicator.style.cssText = `
                position: fixed;
                top: 10px;
                right: 10px;
                background: rgba(52, 152, 219, 0.9);
                color: white;
                padding: 8px 12px;
                border-radius: 5px;
                font-size: 12px;
                z-index: 1000;
                box-shadow: 0 2px 5px rgba(0,0,0,0.2);
            `;
            document.body.appendChild(refreshIndicator);
        }
        refreshIndicator.textContent = `Auto-refresh ON | Last: ${now}`;
    }
    
    async logout() {
        try {
            // Set flag for new session on next login
            sessionStorage.setItem('new_login', 'true');
            
            await fetch('/auth/logout', { method: 'POST' });
            window.location.href = '/login';
        } catch (error) {
            console.error('Logout error:', error);
            // Force redirect even if logout fails
            sessionStorage.setItem('new_login', 'true');
            window.location.href = '/login';
        }
    }
    
    async refreshAnalytics() {
        if (!this.currentAdvertiser) return;
        
        try {
            await Promise.all([
                this.loadStatistics(),
                this.loadAdPerformance(),
                this.loadRecentClicks()
            ]);
        } catch (error) {
            console.error('Error refreshing analytics:', error);
        }
    }
    
    async loadStatistics() {
        try {
            console.log('Loading stats for advertiser:', this.currentAdvertiser.id);
            const response = await fetch(`/advertiser/${this.currentAdvertiser.id}/stats`);
            if (!response.ok) {
                console.error('Stats response not OK:', response.status, response.statusText);
                throw new Error('Failed to load stats');
            }
            
            const stats = await response.json();
            console.log('Received stats:', stats);
            this.updateStatistics(stats);
            this.updateRiskDistribution(stats);
            this.updateFinancialImpact(stats);
            
            // Update refresh indicator
            this.updateRefreshIndicator('analytics');
        } catch (error) {
            console.error('Error loading statistics:', error);
            this.showError('total-clicks', 'Error loading stats');
        }
    }
    
    updateStatistics(stats) {
        const totalClicks = stats.total_clicks || 0;
        const fraudClicks = stats.fraud_clicks || 0;
        const genuineClicks = stats.genuine_clicks || 0;
        const fraudRate = totalClicks > 0 ? ((fraudClicks / totalClicks) * 100).toFixed(1) : 0;
        
        document.getElementById('total-clicks').textContent = totalClicks.toLocaleString();
        document.getElementById('genuine-clicks').textContent = genuineClicks.toLocaleString();
        document.getElementById('fraud-clicks').textContent = fraudClicks.toLocaleString();
        document.getElementById('fraud-rate').textContent = fraudRate + '%';
    }
    
    async loadAdPerformance() {
        try {
            const response = await fetch(`/advertiser/${this.currentAdvertiser.id}/stats`);
            if (!response.ok) throw new Error('Failed to load ad performance');
            
            const stats = await response.json();
            this.updateAdPerformance(stats.ads || []);
        } catch (error) {
            console.error('Error loading ad performance:', error);
            this.showError('ad-performance-container', 'Failed to load ad performance');
        }
    }
    
    updateAdPerformance(ads) {
        const container = document.getElementById('ad-performance-container');
        
        if (ads.length === 0) {
            container.innerHTML = '<div class="loading">No ads found. Create your first ad!</div>';
            return;
        }
        
        const html = `
            <div class="ad-performance-grid">
                ${ads.map(ad => `
                    <div class="ad-card">
                        <h4>${ad.title}</h4>
                        <div class="ad-metrics">
                            <div class="ad-metric">
                                <div class="ad-metric-value">${(ad.clicks || 0).toLocaleString()}</div>
                                <div class="ad-metric-label">Total Clicks</div>
                            </div>
                            <div class="ad-metric">
                                <div class="ad-metric-value">${ad.fraud_clicks || 0}</div>
                                <div class="ad-metric-label">Fraud Clicks</div>
                            </div>
                            <div class="ad-metric">
                                <div class="ad-metric-value">${ad.clicks > 0 ? (((ad.fraud_clicks || 0) / ad.clicks) * 100).toFixed(1) : 0}%</div>
                                <div class="ad-metric-label">Fraud Rate</div>
                            </div>
                        </div>
                    </div>
                `).join('')}
            </div>
        `;
        
        container.innerHTML = html;
    }
    
    async loadRecentClicks() {
        try {
            console.log('Loading sessions for advertiser:', this.currentAdvertiser.id);
            const response = await fetch(`/advertiser/${this.currentAdvertiser.id}/clicks?limit=50`);
            if (!response.ok) {
                console.error('Sessions response not OK:', response.status, response.statusText);
                const errorText = await response.text();
                console.error('Error details:', errorText);
                throw new Error('Failed to load sessions');
            }
            
            const data = await response.json();
            console.log('Received sessions:', data.clicks?.length || 0, 'sessions');
            console.log('Session data:', data.clicks);
            this.updateRecentClicks(data.clicks || []);
        } catch (error) {
            console.error('Error loading recent sessions:', error);
            document.querySelector('#clicks-table tbody').innerHTML = 
                '<tr><td colspan="8" class="error">Failed to load recent sessions</td></tr>';
        }
    }
    
    updateRecentClicks(sessions) {
        const tbody = document.querySelector('#clicks-table tbody');
        
        if (sessions.length === 0) {
            tbody.innerHTML = '<tr><td colspan="8" class="loading">No sessions recorded yet</td></tr>';
            return;
        }
        
        const html = sessions.map(session => {
            // Display IST time directly without conversion
            const sessionTime = session.last_updated;
            const statusClass = session.is_fraud ? 'status-fraud' : 'status-genuine';
            const statusText = session.is_fraud ? 'Fraud' : 'Genuine';
            const riskClass = `risk-${session.risk_level.toLowerCase()}`;
            
            return `
                <tr>
                    <td>${sessionTime}</td>
                    <td>${session.ad_title}</td>
                    <td><code>${session.session_id.substring(0, 12)}...</code></td>
                    <td>${session.clicks_per_session}</td>
                    <td>${session.min_gap.toFixed(2)}s</td>
                    <td>${session.max_gap.toFixed(2)}s</td>
                    <td><span class="status-badge ${statusClass}">${statusText}</span></td>
                    <td><span class="${riskClass}">${session.risk_level}</span></td>
                </tr>
            `;
        }).join('');
        
        tbody.innerHTML = html;
    }
    
    async calculateRiskDistribution() {
        try {
            const response = await fetch(`/advertiser/${this.currentAdvertiser.id}/clicks?limit=100`);
            if (!response.ok) return;
            
            const data = await response.json();
            const clicks = data.clicks || [];
            
            const riskCounts = {
                low: clicks.filter(c => c.risk_level === 'Low').length,
                medium: clicks.filter(c => c.risk_level === 'Medium').length,
                high: clicks.filter(c => c.risk_level === 'High').length
            };
            
            const total = clicks.length;
            
            if (total > 0) {
                const lowPercent = (riskCounts.low / total) * 100;
                const mediumPercent = (riskCounts.medium / total) * 100;
                const highPercent = (riskCounts.high / total) * 100;
                
                document.getElementById('low-risk-fill').style.width = lowPercent + '%';
                document.getElementById('medium-risk-fill').style.width = mediumPercent + '%';
                document.getElementById('high-risk-fill').style.width = highPercent + '%';
                
                document.getElementById('low-risk-count').textContent = riskCounts.low;
                document.getElementById('medium-risk-count').textContent = riskCounts.medium;
                document.getElementById('high-risk-count').textContent = riskCounts.high;
            }
        } catch (error) {
            console.error('Error calculating risk distribution:', error);
        }
    }
    
    updateRiskDistribution(stats) {
        this.calculateRiskDistribution();
    }
    
    updateFinancialImpact(stats) {
        const costPerClick = 0.50;
        const fraudClicks = stats.fraud_clicks || 0;
        const genuineClicks = stats.genuine_clicks || 0;
        
        const moneyLost = fraudClicks * costPerClick;
        const moneySaved = genuineClicks * costPerClick;
        
        document.getElementById('money-lost').textContent = '$' + moneyLost.toFixed(2);
        document.getElementById('money-saved').textContent = '$' + moneySaved.toFixed(2);
    }
    
    async loadMyAds() {
        try {
            const response = await fetch('/ads/my-ads');
            if (!response.ok) throw new Error('Failed to load ads');
            
            const data = await response.json();
            this.displayMyAds(data.ads || []);
            
            // Update refresh indicator
            this.updateRefreshIndicator('ads');
        } catch (error) {
            console.error('Error loading ads:', error);
            this.showError('ads-container', 'Failed to load your ads');
        }
    }
    
    displayMyAds(ads) {
        const container = document.getElementById('ads-container');
        
        if (ads.length === 0) {
            container.innerHTML = `
                <div class="loading">
                    <p>You haven't created any ads yet.</p>
                    <p>Click the "Create Ad" tab to get started!</p>
                </div>
            `;
            return;
        }
        
        const html = `
            <div class="ads-grid">
                ${ads.map(ad => {
                    const fraudRate = ad.total_clicks > 0 ? ((ad.fraud_clicks / ad.total_clicks) * 100).toFixed(1) : 0;
                    return `
                    <div class="ad-item">
                        <h3>${ad.title}</h3>
                        <p>${ad.description}</p>
                        <div class="ad-status ${ad.is_active ? 'active' : 'inactive'}">
                            ${ad.is_active ? 'Active' : 'Inactive'}
                        </div>
                        <div class="ad-stats">
                            <div class="ad-stat">
                                <div class="ad-stat-value">${ad.total_clicks || 0}</div>
                                <div class="ad-stat-label">Clicks</div>
                            </div>
                            <div class="ad-stat">
                                <div class="ad-stat-value">${ad.fraud_clicks || 0}</div>
                                <div class="ad-stat-label">Fraud</div>
                            </div>
                            <div class="ad-stat">
                                <div class="ad-stat-value">${fraudRate}%</div>
                                <div class="ad-stat-label">Fraud Rate</div>
                            </div>
                        </div>
                        <div style="margin-top: 1rem; font-size: 0.9rem; color: #6c757d;">
                            <strong>Target:</strong> <a href="${ad.target_url}" target="_blank">${ad.target_url}</a>
                        </div>
                    </div>
                `}).join('')}
            </div>
        `;
        
        container.innerHTML = html;
    }
    
    async createAd() {
        const form = document.getElementById('create-ad-form');
        const formData = new FormData(form);
        const messageEl = document.getElementById('create-ad-message');
        const submitBtn = document.getElementById('create-ad-btn');
        
        // Hide previous messages
        messageEl.style.display = 'none';
        
        // Disable submit button
        submitBtn.disabled = true;
        submitBtn.textContent = 'Creating...';
        
        try {
            const adData = {
                title: formData.get('title'),
                description: formData.get('description'),
                image_url: formData.get('image_url') || '',
                target_url: formData.get('target_url')
            };
            
            const response = await fetch('/ads/create', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(adData)
            });
            
            const result = await response.json();
            
            if (response.ok) {
                messageEl.textContent = 'Ad created successfully!';
                messageEl.className = 'message success';
                messageEl.style.display = 'block';
                
                // Reset form
                form.reset();
                
                // Switch to ads tab to show the new ad
                setTimeout(() => {
                    this.switchTab('ads');
                }, 1500);
            } else {
                throw new Error(result.detail || 'Failed to create ad');
            }
        } catch (error) {
            messageEl.textContent = error.message;
            messageEl.className = 'message error';
            messageEl.style.display = 'block';
        } finally {
            submitBtn.disabled = false;
            submitBtn.textContent = 'Create Advertisement';
        }
    }
    
    toggleAutoRefresh() {
        const button = document.getElementById('auto-refresh-btn');
        
        if (this.isAutoRefresh) {
            // Stop all auto-refresh
            this.stopTabRefresh('analytics');
            this.stopTabRefresh('ads');
            this.isAutoRefresh = false;
            button.textContent = '⏱️ Auto Refresh: OFF';
            button.classList.remove('active');
            
            // Hide refresh indicator
            const indicator = document.getElementById('refresh-indicator');
            if (indicator) {
                indicator.style.display = 'none';
            }
        } else {
            // Start auto-refresh for current tab
            this.isAutoRefresh = true;
            button.textContent = '⏱️ Auto Refresh: ON';
            button.classList.add('active');
            
            // Start refresh for current tab
            this.startTabRefresh(this.currentTab);
            
            // Show refresh indicator
            const indicator = document.getElementById('refresh-indicator');
            if (indicator) {
                indicator.style.display = 'block';
            }
        }
    }
    
    showError(elementId, message) {
        const element = document.getElementById(elementId);
        if (element) {
            element.innerHTML = `<div class="error">${message}</div>`;
        }
    }
}

// Initialize dashboard when page loads
document.addEventListener('DOMContentLoaded', () => {
    new AdvertiserDashboard();
});