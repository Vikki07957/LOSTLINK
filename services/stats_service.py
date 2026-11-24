"""
LOSTLINK - Analytics and Statistics Service
Aggregates platform metrics, recovery rates, category trends, and activity logs.
"""

from datetime import datetime
from db import get_db, to_object_id, serialize_docs
from config import Config

def get_platform_statistics():
    """Retrieve system-wide numbers for landing page and admin dashboard."""
    db = get_db()
    
    total_lost = db.items.count_documents({"type": "lost"})
    total_found = db.items.count_documents({"type": "found"})
    total_items = total_lost + total_found
    
    # Recovered items
    recovered_items = db.items.count_documents({
        "$or": [
            {"status": "Recovered"},
            {"status": "Returned to Owner"}
        ]
    })
    
    # Claims
    total_claims = db.claims.count_documents({})
    pending_claims = db.claims.count_documents({"status": "Pending"})
    approved_claims = db.claims.count_documents({"status": "Approved"})
    
    # Users
    total_users = db.users.count_documents({})
    
    # Recovery rate percentage
    recovery_rate = 0
    if total_lost > 0:
        recovery_rate = int(round((recovered_items / total_lost) * 100))
        
    return {
        "total_lost": total_lost,
        "total_found": total_found,
        "total_items": total_items,
        "recovered_items": recovered_items,
        "recovery_rate": min(100, recovery_rate),
        "total_claims": total_claims,
        "pending_claims": pending_claims,
        "approved_claims": approved_claims,
        "total_users": total_users
    }

def get_category_distribution():
    """Calculate items count per category for Chart.js rendering."""
    db = get_db()
    categories_cfg = Config.CATEGORIES
    
    labels = []
    lost_counts = []
    found_counts = []
    
    for cat in categories_cfg:
        cat_id = cat["id"]
        labels.append(cat["name"].split("&")[0].strip())
        l_cnt = db.items.count_documents({"category": cat_id, "type": "lost"})
        f_cnt = db.items.count_documents({"category": cat_id, "type": "found"})
        lost_counts.append(l_cnt)
        found_counts.append(f_cnt)
        
    return {
        "labels": labels,
        "lost_counts": lost_counts,
        "found_counts": found_counts
    }

def get_recent_activity_logs(limit=10):
    """Retrieve chronological recent audit and system events."""
    db = get_db()
    logs = list(db.activity_logs.find().sort("timestamp", -1).limit(limit))
    return serialize_docs(logs)

def log_activity(action, description, user_name="System", item_id=None, item_title=None):
    """Record an audit event."""
    db = get_db()
    event = {
        "action": action,
        "description": description,
        "user_name": user_name,
        "item_id": str(item_id) if item_id else None,
        "item_title": item_title,
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
    db.activity_logs.insert_one(event)

def get_user_dashboard_stats(user_id):
    """Compute personalized statistics for a logged-in user."""
    db = get_db()
    uid_str = str(user_id)
    
    my_lost_count = db.items.count_documents({"reporter_id": uid_str, "type": "lost"})
    my_found_count = db.items.count_documents({"reporter_id": uid_str, "type": "found"})
    
    my_recovered_count = db.items.count_documents({
        "reporter_id": uid_str,
        "status": {"$in": ["Recovered", "Returned to Owner"]}
    })
    
    # Claims submitted by me
    my_claims_submitted = db.claims.count_documents({"claimant_id": uid_str})
    
    # Claims received on items I reported as found
    my_found_items = list(db.items.find({"reporter_id": uid_str, "type": "found"}))
    my_found_ids = [str(item["_id"]) for item in my_found_items]
    
    claims_received_count = 0
    if my_found_ids:
        claims_received_count = db.claims.count_documents({"item_id": {"$in": my_found_ids}})
        
    return {
        "my_lost_count": my_lost_count,
        "my_found_count": my_found_count,
        "my_recovered_count": my_recovered_count,
        "my_claims_submitted": my_claims_submitted,
        "claims_received_count": claims_received_count
    }
