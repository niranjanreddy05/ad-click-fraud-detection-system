# Ad Click Fraud Detection System - Demo Guide

## 🚀 PHASE 11: Real-Time Demo

### System Overview
This system demonstrates real-time ad click fraud detection using machine learning. It consists of:

1. **User Platform** (http://127.0.0.1:8000) - Where users see content and ads
2. **Advertiser Dashboard** (http://127.0.0.1:8000/advertiser) - Where advertisers monitor fraud
3. **ML Backend** - Real-time fraud detection API

### Demo Scenarios

#### Scenario 1: Normal User Behavior
**What to do:**
1. Open the User Platform (http://127.0.0.1:8000)
2. Click on ads naturally with 5-10 second gaps
3. Click different ads, not the same one repeatedly
4. Observe the session info updating

**Expected Results:**
- Low fraud probability (< 30%)
- Risk Level: Low
- Status: Genuine

#### Scenario 2: Suspicious Behavior
**What to do:**
1. Click the same ad multiple times quickly (< 2 seconds apart)
2. Accumulate 10+ clicks in the same session
3. Keep clicking rapidly

**Expected Results:**
- Medium fraud probability (30-70%)
- Risk Level: Medium
- Status: May show as Fraud

#### Scenario 3: Bot-like Behavior
**What to do:**
1. Click the "🤖 Simulate Bot Clicks" button
2. Or use Ctrl+B keyboard shortcut
3. Watch rapid automated clicking

**Expected Results:**
- High fraud probability (> 70%)
- Risk Level: High
- Status: Fraud

### Monitoring Fraud Detection

#### Advertiser Dashboard Features:
1. **Real-time Statistics**
   - Total clicks, genuine vs fraudulent
   - Fraud rate percentage
   - Financial impact calculation

2. **Per-Ad Performance**
   - Click counts per advertisement
   - Fraud rates by ad

3. **Recent Clicks Table**
   - Real-time click log
   - Fraud probability for each click
   - Risk level classification

4. **Risk Distribution**
   - Visual breakdown of risk levels
   - Financial impact metrics

### Key Demo Points

#### 1. Behavioral Pattern Detection
- **Time Gaps**: Clicks < 1 second apart are suspicious
- **Session Frequency**: > 10 clicks per session raises flags
- **User Agent**: Bot-like agents get higher fraud scores

#### 2. Real-time Processing
- Every click is analyzed instantly
- Results appear in advertiser dashboard immediately
- No batch processing delays

#### 3. Financial Impact
- Shows money lost to fraudulent clicks
- Demonstrates ROI of fraud detection
- Cost per click: $0.50 (configurable)

### Demo Script for Presentation

#### Opening (2 minutes)
"This system detects fraudulent ad clicks in real-time using machine learning. Let me show you how it works."

#### User Behavior Demo (3 minutes)
1. "First, let's see normal user behavior"
   - Click ads naturally, show low fraud scores
2. "Now suspicious behavior"
   - Click rapidly, show increasing fraud probability
3. "Finally, bot behavior"
   - Use bot simulator, show high fraud detection

#### Advertiser View (3 minutes)
1. Switch to advertiser dashboard
2. Show real-time updates
3. Explain financial impact
4. Demonstrate auto-refresh feature

#### Technical Explanation (2 minutes)
1. "The ML model analyzes 4 key features:"
   - Clicks per session
   - Time between clicks
   - Session duration
   - User agent type
2. "Results are classified as Low/Medium/High risk"
3. "All data is stored for historical analysis"

### Common Demo Issues & Solutions

#### Issue: No model loaded
**Solution:** Run `python mock_model.py` to create test model

#### Issue: Database errors
**Solution:** Run `python database.py` to reinitialize

#### Issue: Ads not loading
**Solution:** Check server logs, restart with `python main.py`

#### Issue: Frontend not updating
**Solution:** Hard refresh browser (Ctrl+F5)

### Advanced Demo Features

#### Auto-refresh Dashboard
- Enable auto-refresh in advertiser dashboard
- Shows real-time updates every 5 seconds
- Demonstrates live monitoring capability

#### Session Tracking
- Each browser session gets unique ID
- Tracks cumulative behavior
- Shows session duration and click patterns

#### Risk Level Visualization
- Color-coded risk indicators
- Progress bars for risk distribution
- Financial impact calculations

### Demo Customization

#### Adjusting Fraud Thresholds
Edit `mock_model.py` to change detection sensitivity:
```python
# More sensitive (catches more fraud)
if clicks_per_session > 5:  # Instead of 10
    fraud_score += 0.4

# Less sensitive (fewer false positives)
if time_gap_seconds < 0.2:  # Instead of 1.0
    fraud_score += 0.4
```

#### Changing Cost Per Click
Edit `advertiser_dashboard.js`:
```javascript
const costPerClick = 1.00; // Instead of 0.50
```

### Performance Metrics to Highlight

1. **Detection Speed**: < 100ms per click
2. **Accuracy**: Catches obvious bot behavior
3. **Real-time Updates**: Instant dashboard refresh
4. **Scalability**: SQLite handles demo load easily
5. **User Experience**: Seamless for genuine users

### Questions & Answers Preparation

**Q: How accurate is the fraud detection?**
A: The demo model uses rule-based detection. Your Colab model will have actual ML accuracy metrics.

**Q: Can this handle high traffic?**
A: Yes, FastAPI is production-ready. For scale, upgrade to PostgreSQL and add caching.

**Q: What about false positives?**
A: The system uses probability scores, not binary decisions. Advertisers can set their own thresholds.

**Q: How does this save money?**
A: By identifying fraudulent clicks, advertisers avoid paying for fake traffic and can optimize their ad spend.

### Next Steps After Demo

1. **Import Real Model**: Replace mock model with your trained Colab model
2. **Add More Features**: Include IP analysis, device fingerprinting
3. **Enhance UI**: Add charts, better visualizations
4. **Scale Database**: Move to PostgreSQL for production
5. **Add Authentication**: Secure advertiser access
6. **API Rate Limiting**: Prevent abuse of prediction endpoint

### Demo Success Criteria

✅ Shows clear difference between genuine and fraudulent clicks
✅ Real-time updates work smoothly
✅ Financial impact is clearly demonstrated
✅ System handles both manual and automated testing
✅ Advertiser dashboard provides actionable insights
✅ Technical architecture is explained clearly