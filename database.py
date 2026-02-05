"""
Database models and initialization for Ad Click Fraud Detection System
Uses SQLite for demo-friendly local storage
"""
import sqlite3
import os
import hashlib
import pytz
from datetime import datetime
from typing import List, Dict, Any, Optional

DATABASE_PATH = "fraud_detection.db"

def init_database():
    """Initialize the SQLite database with required tables"""
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    
    # Advertisers table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS advertisers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # Ads table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS ads (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            advertiser_id INTEGER NOT NULL,
            title TEXT NOT NULL,
            description TEXT,
            image_url TEXT,
            target_url TEXT,
            is_active BOOLEAN DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (advertiser_id) REFERENCES advertisers (id)
        )
    """)
    
    # Click logs table - stores every click with fraud analysis
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS click_logs (
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
        )
    """)
    
    # Session summary table - one record per session
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS session_summary (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT UNIQUE NOT NULL,
            ad_id INTEGER NOT NULL,
            advertiser_id INTEGER NOT NULL,
            ad_title TEXT NOT NULL,
            clicks_per_session INTEGER NOT NULL,
            session_duration_minutes REAL NOT NULL,
            min_gap REAL NOT NULL,
            max_gap REAL NOT NULL,
            is_fraud BOOLEAN NOT NULL,
            fraud_probability REAL NOT NULL,
            risk_level TEXT NOT NULL,
            model_used TEXT NOT NULL,
            last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (ad_id) REFERENCES ads (id),
            FOREIGN KEY (advertiser_id) REFERENCES advertisers (id)
        )
    """)
    
    # Create indexes for better performance
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_clicks_ad_id ON click_logs(ad_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_clicks_session ON click_logs(session_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_clicks_fraud ON click_logs(is_fraud)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_clicks_date ON click_logs(clicked_at)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_session_summary_advertiser ON session_summary(advertiser_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_session_summary_session ON session_summary(session_id)")
    
    conn.commit()
    conn.close()
    print("Database initialized successfully")

def insert_sample_data():
    """Insert sample advertisers and ads for demo"""
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    
    # Sample advertisers with hashed passwords (password: "demo123")
    password_hash = hashlib.sha256("demo123".encode()).hexdigest()
    advertisers = [
        ("TechCorp", "ads@techcorp.com", password_hash),
        ("FashionBrand", "marketing@fashionbrand.com", password_hash),
        ("GameStudio", "promo@gamestudio.com", password_hash)
    ]
    
    cursor.executemany(
        "INSERT OR IGNORE INTO advertisers (name, email, password_hash) VALUES (?, ?, ?)",
        advertisers
    )
    
    # Sample ads
    ads = [
        (1, "Latest Smartphone", "Revolutionary new phone with AI features", 
         "/static/images/phone.jpg", "https://techcorp.com/phone"),
        (1, "Laptop Sale", "50% off premium laptops this week", 
         "/static/images/laptop.jpg", "https://techcorp.com/laptops"),
        (2, "Summer Collection", "Trendy clothes for the season", 
         "/static/images/fashion.jpg", "https://fashionbrand.com/summer"),
        (2, "Designer Shoes", "Luxury footwear collection", 
         "/static/images/shoes.jpg", "https://fashionbrand.com/shoes"),
        (3, "New RPG Game", "Epic adventure awaits in our latest game", 
         "/static/images/game.jpg", "https://gamestudio.com/rpg"),
        (3, "Mobile Puzzle", "Addictive puzzle game for mobile", 
         "/static/images/puzzle.jpg", "https://gamestudio.com/puzzle")
    ]
    
    cursor.executemany(
        "INSERT OR IGNORE INTO ads (advertiser_id, title, description, image_url, target_url) VALUES (?, ?, ?, ?, ?)",
        ads
    )
    
    conn.commit()
    conn.close()
    print("Sample data inserted successfully")

def get_ads() -> List[Dict[str, Any]]:
    """Get all active ads"""
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT a.*, adv.name as advertiser_name 
        FROM ads a 
        JOIN advertisers adv ON a.advertiser_id = adv.id 
        WHERE a.is_active = 1
        ORDER BY a.created_at DESC
    """)
    
    ads = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return ads

# def log_click(ad_id: int, advertiser_id: int, session_id: str, clicks_per_session: int, 
#               time_gap_seconds: float, session_duration_minutes: float,
#               user_agent_category: int, is_fraud: bool, fraud_probability: float,
#               risk_level: str, model_used: str) -> int:
#     """Log a click with fraud analysis results"""
#     conn = sqlite3.connect(DATABASE_PATH)
#     cursor = conn.cursor()
    
#     cursor.execute("""
#         INSERT INTO click_logs 
#         (ad_id, advertiser_id, session_id, clicks_per_session, time_gap_seconds, 
#          session_duration_minutes, user_agent_category, is_fraud, 
#          fraud_probability, risk_level, model_used)
#         VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
#     """, (ad_id, advertiser_id, session_id, clicks_per_session, time_gap_seconds,
#           session_duration_minutes, user_agent_category, is_fraud,
#           fraud_probability, risk_level, model_used))
    
#     click_id = cursor.lastrowid
#     conn.commit()
#     conn.close()
#     return click_id
def log_click(ad_id: int, advertiser_id: int, session_id: str, clicks_per_session: int, 
              time_gap_seconds: float, session_duration_minutes: float,
              user_agent_category: int, is_fraud: bool, fraud_probability: float,
              risk_level: str, model_used: str) -> int:
    """Log a click with fraud analysis results and update session summary"""

    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()

    # Generate IST timestamp
    ist = pytz.timezone("Asia/Kolkata")
    clicked_at = datetime.now(ist).strftime("%Y-%m-%d %H:%M:%S")

    # Log individual click
    cursor.execute("""
        INSERT INTO click_logs 
        (ad_id, advertiser_id, session_id, clicks_per_session, time_gap_seconds, 
         session_duration_minutes, user_agent_category, is_fraud, 
         fraud_probability, risk_level, model_used, clicked_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        ad_id, advertiser_id, session_id, clicks_per_session,
        time_gap_seconds, session_duration_minutes,
        user_agent_category, is_fraud,
        fraud_probability, risk_level, model_used,
        clicked_at
    ))

    click_id = cursor.lastrowid
    
    # Update session summary
    update_session_summary(cursor, session_id, ad_id, advertiser_id, clicks_per_session,
                          session_duration_minutes, time_gap_seconds, is_fraud,
                          fraud_probability, risk_level, model_used)
    
    conn.commit()
    conn.close()
    return click_id

def update_session_summary(cursor, session_id: str, ad_id: int, advertiser_id: int,
                          clicks_per_session: int, session_duration_minutes: float,
                          time_gap_seconds: float, is_fraud: bool, fraud_probability: float,
                          risk_level: str, model_used: str):
    """Update or create session summary with min/max gap tracking and fraud persistence"""
    
    # Get ad title
    cursor.execute("SELECT title FROM ads WHERE id = ?", (ad_id,))
    ad_title = cursor.fetchone()[0]
    
    # Check if session exists
    cursor.execute("SELECT min_gap, max_gap, is_fraud FROM session_summary WHERE session_id = ?", (session_id,))
    existing = cursor.fetchone()
    
    if existing:
        current_min_gap, current_max_gap, existing_fraud = existing
        
        # Update min/max gaps - only update min_gap if current gap is positive
        new_min_gap = min(current_min_gap, time_gap_seconds) if time_gap_seconds > 0 else current_min_gap
        new_max_gap = max(current_max_gap, time_gap_seconds)
        
        # Once fraud is detected, it stays fraud
        final_is_fraud = existing_fraud or is_fraud
        final_fraud_prob = fraud_probability if final_is_fraud else fraud_probability
        final_risk_level = risk_level if final_is_fraud else risk_level
        
        cursor.execute("""
            UPDATE session_summary SET
                clicks_per_session = ?,
                session_duration_minutes = ?,
                min_gap = ?,
                max_gap = ?,
                is_fraud = ?,
                fraud_probability = ?,
                risk_level = ?,
                model_used = ?,
                last_updated = ?
            WHERE session_id = ?
        """, (clicks_per_session, session_duration_minutes, new_min_gap, new_max_gap,
              final_is_fraud, final_fraud_prob, final_risk_level, model_used, 
              datetime.now(pytz.timezone("Asia/Kolkata")).strftime("%Y-%m-%d %H:%M:%S"),
              session_id))
    else:
        # Create new session summary - first click has 0 gap
        cursor.execute("""
            INSERT INTO session_summary 
            (session_id, ad_id, advertiser_id, ad_title, clicks_per_session,
             session_duration_minutes, min_gap, max_gap, is_fraud,
             fraud_probability, risk_level, model_used)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (session_id, ad_id, advertiser_id, ad_title, clicks_per_session,
              session_duration_minutes, 999999, 0,
              is_fraud, fraud_probability, risk_level, model_used))


def get_advertiser_stats(advertiser_id: int) -> Dict[str, Any]:
    """Get click statistics for an advertiser"""
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    # Overall stats
    cursor.execute("""
        SELECT 
            COUNT(*) as total_clicks,
            SUM(CASE WHEN is_fraud = 1 THEN 1 ELSE 0 END) as fraud_clicks,
            SUM(CASE WHEN is_fraud = 0 THEN 1 ELSE 0 END) as genuine_clicks,
            AVG(fraud_probability) as avg_fraud_prob
        FROM click_logs cl
        JOIN ads a ON cl.ad_id = a.id
        WHERE a.advertiser_id = ?
    """, (advertiser_id,))
    
    stats = dict(cursor.fetchone())
    
    # Per-ad breakdown
    cursor.execute("""
        SELECT 
            a.id, a.title,
            COUNT(*) as clicks,
            SUM(CASE WHEN cl.is_fraud = 1 THEN 1 ELSE 0 END) as fraud_clicks,
            AVG(cl.fraud_probability) as avg_fraud_prob
        FROM ads a
        LEFT JOIN click_logs cl ON a.id = cl.ad_id
        WHERE a.advertiser_id = ?
        GROUP BY a.id, a.title
        ORDER BY clicks DESC
    """, (advertiser_id,))
    
    stats['ads'] = [dict(row) for row in cursor.fetchall()]
    
    conn.close()
    return stats

def get_recent_clicks(advertiser_id: int, limit: int = 50) -> List[Dict[str, Any]]:
    """Get recent session summaries for an advertiser"""
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    try:
        print(f"Querying session_summary for advertiser_id: {advertiser_id}")
        cursor.execute("""
            SELECT *
            FROM session_summary
            WHERE advertiser_id = ?
            ORDER BY last_updated DESC
            LIMIT ?
        """, (advertiser_id, limit))
        
        sessions = [dict(row) for row in cursor.fetchall()]
        print(f"Found {len(sessions)} sessions in database")
        conn.close()
        return sessions
    except Exception as e:
        print(f"Error in get_recent_clicks: {e}")
        conn.close()
        return []

# Authentication functions
def hash_password(password: str) -> str:
    """Hash password using SHA-256"""
    return hashlib.sha256(password.encode()).hexdigest()

def create_advertiser(name: str, email: str, password: str) -> Optional[int]:
    """Create new advertiser account"""
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    
    try:
        password_hash = hash_password(password)
        cursor.execute(
            "INSERT INTO advertisers (name, email, password_hash) VALUES (?, ?, ?)",
            (name, email, password_hash)
        )
        advertiser_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return advertiser_id
    except sqlite3.IntegrityError:
        conn.close()
        return None  # Email already exists

def authenticate_advertiser(email: str, password: str) -> Optional[Dict[str, Any]]:
    """Authenticate advertiser login"""
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    password_hash = hash_password(password)
    cursor.execute(
        "SELECT id, name, email FROM advertisers WHERE email = ? AND password_hash = ?",
        (email, password_hash)
    )
    
    advertiser = cursor.fetchone()
    conn.close()
    
    return dict(advertiser) if advertiser else None

def get_advertiser_by_id(advertiser_id: int) -> Optional[Dict[str, Any]]:
    """Get advertiser by ID"""
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    cursor.execute(
        "SELECT id, name, email FROM advertisers WHERE id = ?",
        (advertiser_id,)
    )
    
    advertiser = cursor.fetchone()
    conn.close()
    
    return dict(advertiser) if advertiser else None

# Ad management functions
def create_ad(advertiser_id: int, title: str, description: str, image_url: str, target_url: str) -> int:
    """Create new ad for advertiser"""
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    
    cursor.execute("""
        INSERT INTO ads (advertiser_id, title, description, image_url, target_url)
        VALUES (?, ?, ?, ?, ?)
    """, (advertiser_id, title, description, image_url, target_url))
    
    ad_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return ad_id

def get_advertiser_ads(advertiser_id: int) -> List[Dict[str, Any]]:
    """Get all ads for specific advertiser with click statistics"""
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT 
            a.*,
            COALESCE(COUNT(cl.id), 0) as total_clicks,
            COALESCE(SUM(CASE WHEN cl.is_fraud = 1 THEN 1 ELSE 0 END), 0) as fraud_clicks,
            COALESCE(SUM(CASE WHEN cl.is_fraud = 0 THEN 1 ELSE 0 END), 0) as genuine_clicks,
            COALESCE(AVG(cl.fraud_probability), 0) as avg_fraud_prob
        FROM ads a
        LEFT JOIN click_logs cl ON a.id = cl.ad_id
        WHERE a.advertiser_id = ?
        GROUP BY a.id, a.title, a.description, a.image_url, a.target_url, a.is_active, a.created_at
        ORDER BY a.created_at DESC
    """, (advertiser_id,))
    
    ads = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return ads

def get_ad_with_advertiser(ad_id: int) -> Optional[Dict[str, Any]]:
    """Get ad with advertiser info for click tracking"""
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT a.*, adv.name as advertiser_name 
        FROM ads a 
        JOIN advertisers adv ON a.advertiser_id = adv.id 
        WHERE a.id = ?
    """, (ad_id,))
    
    ad = cursor.fetchone()
    conn.close()
    return dict(ad) if ad else None

if __name__ == "__main__":
    print("Initializing database...")
    init_database()
    insert_sample_data()
    
    # Test queries
    print(f"\nTotal ads: {len(get_ads())}")
    print(f"Advertiser 1 stats: {get_advertiser_stats(1)}")
    print("\nDatabase setup complete!")