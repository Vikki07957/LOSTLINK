"""
LOSTLINK - Authentication and User Session Service
Handles secure registration, password hashing, login, and role-based permissions.
"""

from datetime import datetime
from functools import wraps
from flask import session, redirect, url_for, flash, request
from werkzeug.security import generate_password_hash, check_password_hash
from db import get_db, to_object_id, serialize_doc

def register_user(name, email, phone, password, role="user", campus="Main Campus", avatar=None):
    """Register a new user with hashed password."""
    db = get_db()
    email = email.strip().lower()
    
    # Check if user already exists
    existing = db.users.find_one({"email": email})
    if existing:
        return False, "An account with this email address already exists."
    
    if len(password) < 6:
        return False, "Password must be at least 6 characters long."
        
    hashed_pw = generate_password_hash(password)
    new_user = {
        "name": name.strip(),
        "email": email,
        "phone": phone.strip(),
        "campus": campus.strip(),
        "password": hashed_pw,
        "role": role, # 'user' or 'admin'
        "avatar": avatar or f"https://api.dicebear.com/7.x/identicon/svg?seed={email}",
        "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "is_active": True,
        "reputation_score": 100
    }
    
    result = db.users.insert_one(new_user)
    new_user["_id"] = result.inserted_id
    return True, serialize_doc(new_user)

def authenticate_user(email, password):
    """Authenticate user credentials and return user doc if valid."""
    db = get_db()
    email = email.strip().lower()
    user = db.users.find_one({"email": email})
    
    if not user:
        return False, "No account found with this email address."
        
    if not user.get("is_active", True):
        return False, "This account has been suspended by an administrator."
        
    if not check_password_hash(user["password"], password):
        return False, "Incorrect password. Please try again."
        
    return True, serialize_doc(user)

def set_user_session(user):
    """Store user in Flask session."""
    session["user_id"] = str(user["_id"])
    session["user_name"] = user.get("name", "User")
    session["user_email"] = user.get("email", "")
    session["user_role"] = user.get("role", "user")
    session["user_avatar"] = user.get("avatar", "")

def clear_user_session():
    """Clear user session on logout."""
    session.pop("user_id", None)
    session.pop("user_name", None)
    session.pop("user_email", None)
    session.pop("user_role", None)
    session.pop("user_avatar", None)

def get_current_user():
    """Retrieve currently logged in user document from DB."""
    if "user_id" not in session:
        return None
    db = get_db()
    user = db.users.find_one({"_id": to_object_id(session["user_id"])})
    return serialize_doc(user)

def login_required(f):
    """Decorator to require login for protected routes."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "user_id" not in session:
            flash("Please log in to access this page.", "warning")
            return redirect(url_for("login", next=request.url))
        return f(*args, **kwargs)
    return decorated_function

def admin_required(f):
    """Decorator to require admin role for privileged routes."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "user_id" not in session:
            flash("Please log in with administrator privileges.", "warning")
            return redirect(url_for("login", next=request.url))
        if session.get("user_role") != "admin":
            flash("Access denied. Administrator privileges required.", "danger")
            return redirect(url_for("dashboard"))
        return f(*args, **kwargs)
    return decorated_function

def update_user_profile(user_id, name, phone, campus, bio=None):
    """Update user personal details."""
    db = get_db()
    update_data = {
        "name": name.strip(),
        "phone": phone.strip(),
        "campus": campus.strip(),
    }
    if bio is not None:
        update_data["bio"] = bio.strip()
        
    db.users.update_one({"_id": to_object_id(user_id)}, {"$set": update_data})
    session["user_name"] = name.strip()
    return True, "Profile updated successfully."

def change_user_password(user_id, old_password, new_password):
    """Securely update user password."""
    db = get_db()
    user = db.users.find_one({"_id": to_object_id(user_id)})
    if not user:
        return False, "User not found."
    if not check_password_hash(user["password"], old_password):
        return False, "Current password does not match."
    if len(new_password) < 6:
        return False, "New password must be at least 6 characters long."
        
    new_hashed = generate_password_hash(new_password)
    db.users.update_one({"_id": to_object_id(user_id)}, {"$set": {"password": new_hashed}})
    return True, "Password changed successfully."
