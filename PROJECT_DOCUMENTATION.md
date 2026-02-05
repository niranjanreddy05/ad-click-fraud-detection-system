# Ad Click Fraud Detection System - Complete Implementation Guide

## 📋 Table of Contents
1. [Project Overview](#project-overview)
2. [System Architecture](#system-architecture)
3. [Data Flow](#data-flow)
4. [Database Schema](#database-schema)
5. [Implementation Details](#implementation-details)
6. [Setup & Installation](#setup--installation)
7. [Usage Guide](#usage-guide)
8. [API Documentation](#api-documentation)
9. [Key Features](#key-features)
10. [Testing](#testing)

---

## 🎯 Project Overview

**Ad Click Fraud Detection System** is a full-stack machine learning application that detects fraudulent ad clicks in real-time using behavioral analysis and ML models.

### Tech Stack
- **Backend**: FastAPI (Python)
- **Frontend**: HTML, CSS, JavaScript
- **Database**: SQLite
- **ML Model**: XGBoost (trained in Google Colab)
- **Timezone**: Indian Standard Time (IST)

### Project Structure
```
Ad Click Fraud/
├── main.py                          # FastAPI backend server
├── database.py                      # Database models & operations
├── feature_builder.py               # ML feature engineering
├── requirements.txt                 # Python dependencies
├── check_gaps.py                    # Verification script
├── check_fraud.py                   # Fraud verification script
├── training/
│   ├── xgb_backend_model.pkl       # Trained XGBoost model
│   └── backend_scaler.pkl          # Feature scaler
├── templates/
│   ├── user_dashboard.html         # Content platform UI
│   ├── advertiser_dashboard.html   # Advertiser analytics UI
│   ├── login.html                  # Login page
│   └── signup.html                 # Signup page
├── static/
│   ├── css/
│   │   ├── user_dashboard.css
│   │   └── advertiser_dashboard.css
│   └── js/
│       ├── user_dashboard.js       # Click tracking logic
│       └── advertiser_dashboard.js # Analytics dashboard logic
└── fraud_detection.db              # SQLite database (auto-created)
```

---

## 🏗️ System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        USER PLATFORM                             │
│  (Content Site with Embedded Ads - user_dashboard.html)         │
│                                                                   │
│  • Generates unique session_id on page load                      │
│  • Tracks clicks, time gaps, session duration                    │
│  • Sends click data to /predict API                              │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│                    FASTAPI BACKEND (main.py)                     │
│                                                                   │
│  /predict endpoint:                                               │
│  1. Receives click data (session_id, clicks, time_gap, etc.)    │
│  2. Builds ML features (click_frequency, bot_likelihood, etc.)   │
│  3. Scales features using backend_scaler.pkl                     │
│  4. Predicts fraud using xgb_backend_model.pkl                   │
│  5. Logs to database (click_logs + session_summary)             │
│  6. Returns prediction result                                     │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│                   DATABASE (database.py)                         │
│                                                                   │
│  Tables:                                                          │
│  • advertisers - Advertiser accounts                             │
│  • ads - Advertisement details                                    │
│  • click_logs - Every individual click (raw data)                │
│  • session_summary - One record per session (aggregated)         │
│                                                                   │
│  Key Logic:                                                       │
│  • log_click() - Inserts click + updates session_summary         │
│  • update_session_summary() - Maintains min/max gaps, fraud      │
│    persistence within same session                                │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│              ADVERTISER DASHBOARD                                │
│         (advertiser_dashboard.html)                              │
│                                                                   │
│  • Login/Signup authentication                                    │
│  • View session-based analytics                                   │
│  • One row per session (not per click)                           │
│  • Shows: Time, Ad, Session ID, Clicks, Min Gap, Max Gap,       │
│           Status (Fraud/Genuine), Risk Level                     │
│  • Auto-refreshes every 5 seconds                                │
│  • Create and manage ads                                          │
└─────────────────────────────────────────────────────────────────┘
```

---

## 🔄 Data Flow

### 1. User Clicks Ad (User Platform)

```javascript
// user_dashboard.js - Click Handler
handleAdClick(adId) {
    const now = Date.now();
    const timeGapSeconds = this.lastClickTime ? (now - this.lastClickTime) / 1000 : 0;
    
    this.clickCount++;
    this.lastClickTime = now;
    
    const clickData = {
        session_id: this.sessionId,              // e.g., "session_1769771261439_uiv..."
        clicks_per_session: this.clickCount,     // e.g., 1, 2, 3...
        time_gap_seconds: timeGapSeconds,        // e.g., 0, 2.5, 0.3...
        session_duration_minutes: (now - this.sessionStart) / (1000 * 60),
        ad_id: adId,
        user_agent_category: 1
    };
    
    // Send to backend
    fetch('/predict', {
        method: 'POST',
        body: JSON.stringify(clickData)
    });
}
```

### 2. Backend Processes Click (main.py)

```python
@app.post("/predict")
async def predict(click: ClickData):
    # Step 1: Build ML features
    session_duration = max(click.session_duration_minutes, 1.0)
    click_frequency = click.clicks_per_session / session_duration
    
    X = pd.DataFrame([{
        "click_frequency": click_frequency,
        "time_since_last_click": click.time_gap_seconds,
        "VPN_usage": 0,
        "proxy_usage": 0,
        "bot_likelihood_score": min(click_frequency / 10, 1.0)
    }])
    
    # Step 2: Scale features
    X_scaled = scaler.transform(X)
    
    # Step 3: Predict fraud
    fraud_prob = float(classifier.predict_proba(X_scaled)[0][1])
    is_fraud = fraud_prob >= 0.5
    risk = get_risk_level(fraud_prob)
    
    # Step 4: Log to database
    log_click(
        ad_id=click.ad_id,
        advertiser_id=ad_info["advertiser_id"],
        session_id=click.session_id,
        clicks_per_session=click.clicks_per_session,
        time_gap_seconds=click.time_gap_seconds,
        session_duration_minutes=click.session_duration_minutes,
        user_agent_category=click.user_agent_category,
        is_fraud=is_fraud,
        fraud_probability=fraud_prob,
        risk_level=risk,
        model_used=model_name
    )
    
    return PredictionResponse(...)
```

### 3. Database Updates (database.py)

```python
def log_click(...):
    # Insert into click_logs (every click)
    cursor.execute("""
        INSERT INTO click_logs 
        (ad_id, advertiser_id, session_id, clicks_per_session, 
         time_gap_seconds, ..., clicked_at)
        VALUES (?, ?, ?, ?, ?, ..., ?)
    """, (..., IST_timestamp))
    
    # Update session_summary (one record per session)
    update_session_summary(cursor, session_id, ...)

def update_session_summary(...):
    # Check if session exists
    cursor.execute("SELECT min_gap, max_gap, is_fraud FROM session_summary WHERE session_id = ?")
    existing = cursor.fetchone()
    
    if existing:
        # UPDATE existing session
        new_min_gap = min(current_min_gap, time_gap_seconds) if time_gap_seconds > 0 else current_min_gap
        new_max_gap = max(current_max_gap, time_gap_seconds)
        
        # Fraud persists within same session
        final_is_fraud = existing_fraud or is_fraud
        
        cursor.execute("UPDATE session_summary SET ...")
    else:
        # INSERT new session (first click)
        cursor.execute("""
            INSERT INTO session_summary 
            (session_id, ad_id, advertiser_id, ad_title, clicks_per_session,
             session_duration_minutes, min_gap, max_gap, is_fraud, ...)
            VALUES (?, ?, ?, ?, ?, ?, 999999, 0, ?, ...)
        """)
```

### 4. Advertiser Views Dashboard

```javascript
// advertiser_dashboard.js - Load Sessions
async loadRecentClicks() {
    const response = await fetch(`/advertiser/${advertiser_id}/clicks?limit=50`);
    const data = await response.json();
    
    // Display sessions (one row per session)
    sessions.map(session => `
        <tr>
            <td>${session.last_updated}</td>           // IST timestamp
            <td>${session.ad_title}</td>
            <td>${session.session_id}</td>
            <td>${session.clicks_per_session}</td>
            <td>${session.min_gap.toFixed(2)}s</td>    // Minimum time gap
            <td>${session.max_gap.toFixed(2)}s</td>    // Maximum time gap
            <td>${session.is_fraud ? 'Fraud' : 'Genuine'}</td>
            <td>${session.risk_level}</td>
        </tr>
    `);
}
```

---

## 🗄️ Database Schema

### Table: `advertisers`
```sql
CREATE TABLE advertisers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    email TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### Table: `ads`
```sql
CREATE TABLE ads (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    advertiser_id INTEGER NOT NULL,
    title TEXT NOT NULL,
    description TEXT,
    image_url TEXT,
    target_url TEXT,
    is_active BOOLEAN DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (advertiser_id) REFERENCES advertisers (id)
);
```

### Table: `click_logs` (Raw Click Data)
```sql
CREATE TABLE click_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ad_id INTEGER NOT NULL,
    advertiser_id INTEGER NOT NULL,
    session_id TEXT NOT NULL,
    clicks_per_session INTEGER NOT NULL,
    time_gap_seconds REAL NOT NULL,
    session_duration_minutes REAL NOT NULL,
    user_agent_category INTEGER NOT NULL,
    is_fraud BOOLEAN NOT NULL,
    fraud_probability REAL NOT NULL,
    risk_level TEXT NOT NULL,
    model_used TEXT NOT NULL,
    clicked_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (ad_id) REFERENCES ads (id),
    FOREIGN KEY (advertiser_id) REFERENCES advertisers (id)
);
```

**Example Data:**
```
id | session_id              | clicks | time_gap | is_fraud | clicked_at
1  | session_1769771261439   | 1      | 0.00     | 0        | 2026-01-30 16:30:00
2  | session_1769771261439   | 2      | 2.50     | 0        | 2026-01-30 16:30:02
3  | session_1769771261439   | 3      | 0.30     | 1        | 2026-01-30 16:30:03
4  | session_1769771261439   | 4      | 0.25     | 1        | 2026-01-30 16:30:03
```

### Table: `session_summary` (Aggregated Session Data)
```sql
CREATE TABLE session_summary (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id TEXT UNIQUE NOT NULL,
    ad_id INTEGER NOT NULL,
    advertiser_id INTEGER NOT NULL,
    ad_title TEXT NOT NULL,
    clicks_per_session INTEGER NOT NULL,
    session_duration_minutes REAL NOT NULL,
    min_gap REAL NOT NULL,              -- Minimum time gap (excludes 0)
    max_gap REAL NOT NULL,              -- Maximum time gap
    is_fraud BOOLEAN NOT NULL,          -- Persists once detected
    fraud_probability REAL NOT NULL,
    risk_level TEXT NOT NULL,
    model_used TEXT NOT NULL,
    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (ad_id) REFERENCES ads (id),
    FOREIGN KEY (advertiser_id) REFERENCES advertisers (id)
);
```

**Example Data:**
```
session_id              | clicks | min_gap | max_gap | is_fraud | last_updated
session_1769771261439   | 4      | 0.25    | 2.50    | 1        | 2026-01-30 16:30:03
session_1769771300000   | 1      | 999999  | 0.00    | 0        | 2026-01-30 16:35:00
```

**Key Points:**
- **One row per session** in `session_summary`
- **min_gap**: Minimum non-zero time gap in session
- **max_gap**: Maximum time gap in session
- **is_fraud**: Once fraud detected, stays fraud for that session
- **New session**: Starts fresh with new fraud detection

---

## 🔧 Implementation Details

### Session Management

#### User Platform Session
```javascript
// Generated on page load
generateSessionId() {
    const timestamp = Date.now();
    const random = Math.random().toString(36).substr(2, 9);
    const userSession = this.getUserSessionId();
    return `session_${timestamp}_${random}_${userSession}`;
}

// Reset on logout/login
resetSession() {
    localStorage.removeItem('user_session_id');
    this.sessionId = this.generateSessionId();
    this.sessionStart = Date.now();
    this.clickCount = 0;
    this.lastClickTime = null;
}
```

#### Advertiser Authentication Session
```python
# Login creates session cookie
session_id = str(uuid.uuid4())
sessions[session_id] = {"id": advertiser_id, "name": name, "email": email}
response.set_cookie("session_id", session_id, httponly=True, max_age=86400)
```

### Fraud Detection Logic

#### Feature Engineering
```python
# Features sent to ML model
features = {
    "click_frequency": clicks_per_session / max(session_duration_minutes, 1.0),
    "time_since_last_click": time_gap_seconds,
    "VPN_usage": 0,
    "proxy_usage": 0,
    "bot_likelihood_score": min(click_frequency / 10, 1.0)
}
```

#### Fraud Persistence Rules
1. **Within Same Session**: Once fraud detected, stays fraud
2. **New Session**: Starts fresh, can be genuine
3. **First Click**: time_gap = 0, typically genuine
4. **Rapid Clicks**: Small time gaps → high fraud probability

### Time Gap Calculation

```python
# First click in session
time_gap_seconds = 0
min_gap = 999999  # High initial value
max_gap = 0

# Subsequent clicks
time_gap_seconds = current_time - last_click_time
min_gap = min(current_min_gap, time_gap_seconds) if time_gap_seconds > 0 else current_min_gap
max_gap = max(current_max_gap, time_gap_seconds)
```

### IST Timestamp Handling

```python
# Backend (database.py)
ist = pytz.timezone("Asia/Kolkata")
clicked_at = datetime.now(ist).strftime("%Y-%m-%d %H:%M:%S")

# Frontend (advertiser_dashboard.js)
const sessionTime = session.last_updated;  // Display as-is (IST)
```

---

## 🚀 Setup & Installation

### Prerequisites
```bash
Python 3.8+
pip
```

### Step 1: Install Dependencies
```bash
cd "Ad Click Fraud"
pip install -r requirements.txt
```

**requirements.txt:**
```
fastapi==0.104.1
uvicorn==0.24.0
pydantic==2.5.0
pydantic[email]
joblib==1.3.2
pandas==2.1.3
numpy==1.26.2
scikit-learn==1.3.2
xgboost==2.0.2
pytz==2023.3
```

### Step 2: Initialize Database
```bash
python database.py
```

**Output:**
```
Initializing database...
Database initialized successfully
Sample data inserted successfully

Total ads: 6
Advertiser 1 stats: {...}

Database setup complete!
```

### Step 3: Verify ML Model
```bash
# Check if model files exist
ls training/xgb_backend_model.pkl
ls training/backend_scaler.pkl
```

### Step 4: Start Server
```bash
python main.py
```

**Output:**
```
Starting application...
Loading ML model and preprocessor...
Model expects 5 features
SUCCESS: Model loaded correctly
Database initialized successfully
Sample data inserted successfully
Startup complete
INFO:     Uvicorn running on http://127.0.0.1:8001
```

### Step 5: Access Applications
- **User Platform**: http://127.0.0.1:8001/
- **Advertiser Login**: http://127.0.0.1:8001/login
- **Advertiser Signup**: http://127.0.0.1:8001/signup
- **API Docs**: http://127.0.0.1:8001/docs

---

## 📖 Usage Guide

### For Users (Content Platform)

1. **Open User Platform**: http://127.0.0.1:8001/
2. **View Ads**: Ads are displayed in grid layout
3. **Click Ads**: Click any ad to simulate user behavior
4. **Session Info**: Top-right shows:
   - Session ID
   - Click Count
   - Session Duration
   - Last Click Gap

5. **Bot Simulation** (Demo): Click "🤖 Simulate Bot Clicks" button

### For Advertisers

#### 1. Signup/Login
```
URL: http://127.0.0.1:8001/signup
Email: your@email.com
Password: yourpassword
```

**Demo Account:**
```
Email: ads@techcorp.com
Password: demo123
```

#### 2. View Analytics Dashboard
- **Total Clicks**: All clicks received
- **Genuine Clicks**: Non-fraudulent clicks
- **Fraudulent Clicks**: Detected fraud
- **Fraud Rate**: Percentage of fraud

#### 3. View Session Details
Table shows:
- **Time**: IST timestamp (YYYY-MM-DD HH:MM:SS)
- **Ad**: Ad title
- **Session ID**: Unique session identifier
- **Clicks/Session**: Total clicks in session
- **Min Gap**: Minimum time between clicks (seconds)
- **Max Gap**: Maximum time between clicks (seconds)
- **Status**: Fraud or Genuine
- **Risk Level**: Low, Medium, High

#### 4. Create New Ad
1. Click "Create Ad" tab
2. Fill form:
   - Title
   - Description
   - Image URL (optional)
   - Target URL
3. Click "Create Advertisement"

#### 5. Auto-Refresh
- Enabled by default (refreshes every 5 seconds)
- Toggle with "⏱️ Auto Refresh" button

---

## 📡 API Documentation

### Authentication Endpoints

#### POST /auth/signup
```json
Request:
{
    "name": "Advertiser Name",
    "email": "email@example.com",
    "password": "password123"
}

Response:
{
    "message": "Account created successfully",
    "advertiser_id": 1
}
```

#### POST /auth/login
```json
Request:
{
    "email": "email@example.com",
    "password": "password123"
}

Response:
{
    "message": "Login successful",
    "advertiser": {
        "id": 1,
        "name": "Advertiser Name",
        "email": "email@example.com"
    }
}
```

#### POST /auth/logout
```json
Response:
{
    "message": "Logged out successfully"
}
```

### Fraud Detection Endpoint

#### POST /predict
```json
Request:
{
    "session_id": "session_1769771261439_uiv...",
    "clicks_per_session": 3,
    "time_gap_seconds": 0.5,
    "session_duration_minutes": 0.05,
    "ad_id": 1,
    "user_agent_category": 1
}

Response:
{
    "is_fraud": true,
    "fraud_probability": 0.85,
    "risk_level": "High",
    "model_used": "XGBoost Click Fraud Detection Model"
}
```

### Analytics Endpoints

#### GET /advertiser/{advertiser_id}/stats
```json
Response:
{
    "total_clicks": 100,
    "fraud_clicks": 30,
    "genuine_clicks": 70,
    "avg_fraud_prob": 0.35,
    "ads": [
        {
            "id": 1,
            "title": "Ad Title",
            "clicks": 50,
            "fraud_clicks": 15,
            "avg_fraud_prob": 0.30
        }
    ]
}
```

#### GET /advertiser/{advertiser_id}/clicks?limit=50
```json
Response:
{
    "clicks": [
        {
            "id": 1,
            "session_id": "session_1769771261439_uiv...",
            "ad_id": 1,
            "ad_title": "Ad Title",
            "clicks_per_session": 5,
            "min_gap": 0.25,
            "max_gap": 3.50,
            "is_fraud": 1,
            "fraud_probability": 0.85,
            "risk_level": "High",
            "last_updated": "2026-01-30 16:30:00"
        }
    ]
}
```

### Ad Management Endpoints

#### GET /ads/active
```json
Response:
{
    "ads": [
        {
            "id": 1,
            "advertiser_id": 1,
            "title": "Ad Title",
            "description": "Ad description",
            "image_url": "/static/images/ad.jpg",
            "target_url": "https://example.com",
            "is_active": 1,
            "advertiser_name": "Advertiser Name"
        }
    ]
}
```

#### POST /ads/create
```json
Request:
{
    "title": "New Ad",
    "description": "Ad description",
    "image_url": "https://example.com/image.jpg",
    "target_url": "https://example.com"
}

Response:
{
    "message": "Ad created successfully",
    "ad_id": 10
}
```

---

## ✨ Key Features

### 1. Session-Based Tracking
- ✅ One record per session in advertiser dashboard
- ✅ Updates in real-time as user clicks
- ✅ Tracks min/max time gaps across session
- ✅ New session after logout/login

### 2. Fraud Persistence
- ✅ Once fraud detected in session, stays fraud
- ✅ New session starts fresh (can be genuine)
- ✅ Fraud doesn't carry over to new sessions

### 3. Time Gap Analysis
- ✅ First click: time_gap = 0
- ✅ Min gap: Minimum non-zero gap in session
- ✅ Max gap: Maximum gap in session
- ✅ Excludes zero from min calculation

### 4. IST Timezone
- ✅ All timestamps in Indian Standard Time
- ✅ Backend stores IST
- ✅ Frontend displays IST without conversion

### 5. Real-Time Updates
- ✅ Auto-refresh every 5 seconds
- ✅ Live click tracking
- ✅ Instant fraud detection

### 6. Authentication
- ✅ Secure login/signup
- ✅ Session-based authentication
- ✅ Cookie-based session management

---

## 🧪 Testing

### Test 1: Normal User Behavior
```
1. Open user platform
2. Click ad after 5 seconds
3. Wait 3 seconds, click again
4. Wait 2 seconds, click again

Expected Result:
- Status: Genuine
- Risk Level: Low
- Min Gap: ~2s
- Max Gap: ~5s
```

### Test 2: Suspicious Behavior
```
1. Open user platform
2. Click ad rapidly (< 1 second gaps)
3. Click 5-10 times quickly

Expected Result:
- Status: Fraud
- Risk Level: High
- Min Gap: ~0.3s
- Max Gap: ~1s
```

### Test 3: New Session After Fraud
```
1. Perform Test 2 (fraud detected)
2. Logout from advertiser dashboard
3. Login again
4. Open user platform in new incognito window
5. Click ad normally (5 second gap)

Expected Result:
- New session created
- Status: Genuine (fresh start)
- Risk Level: Low
```

### Test 4: Fraud Persistence in Same Session
```
1. Click ad normally (genuine)
2. Click rapidly 5 times (fraud detected)
3. Wait 10 seconds
4. Click normally again

Expected Result:
- Status: Fraud (persists in same session)
- Min Gap: Updated with new gaps
- Max Gap: Updated with new gaps
```

### Verification Scripts

#### Check Time Gaps
```bash
python check_gaps.py
```

**Output:**
```
CLICK LOGS BY SESSION:

Session: session_1769665608636_uiv...
  Gap: 179.397
  Gap: 2.006
  Gap: 0.328
  Actual Min: 0.328, Max: 179.397

SESSION SUMMARY:
Session: session_1769665608636_uiv..., Stored Min: 0.328, Max: 179.397
```

#### Check Fraud Status
```bash
python check_fraud.py
```

**Output:**
```
Session Data:
Session: session_176977126143..., Clicks: 1, Fraud: 0, Prob: 0.15, Time: 2026-01-30 11:07:43
Session: session_176977124692..., Clicks: 5, Fraud: 1, Prob: 0.95, Time: 2026-01-30 11:07:37
```

---

## 🎯 Summary

### Data Flow Summary
```
User Clicks Ad → Frontend Tracks Session → POST /predict → 
ML Model Predicts → Database Logs (click_logs + session_summary) → 
Advertiser Dashboard Displays (one row per session)
```

### Key Implementation Points
1. **Session ID**: Generated on page load, reset on logout/login
2. **Time Gaps**: First click = 0, subsequent = time since last click
3. **Min/Max Gaps**: Tracked across entire session, excludes zero from min
4. **Fraud Persistence**: Within same session only, new session starts fresh
5. **IST Timestamps**: All times in Indian Standard Time
6. **One Row Per Session**: Advertiser dashboard shows aggregated session data

### Database Tables
- **click_logs**: Every individual click (raw data)
- **session_summary**: One record per session (aggregated, displayed in dashboard)

### Critical Functions
- `log_click()`: Inserts click + updates session summary
- `update_session_summary()`: Maintains min/max gaps + fraud persistence
- `handleAdClick()`: Frontend click tracking
- `predict()`: ML fraud detection

---

## 📞 Support

For issues or questions:
1. Check API docs: http://127.0.0.1:8001/docs
2. Review logs in terminal
3. Verify database: `python check_gaps.py` or `python check_fraud.py`
4. Hard refresh browser: Ctrl + Shift + R

**Project Complete! 🎉**
