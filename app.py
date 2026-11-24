"""
LOSTLINK - Smart Lost & Found Web Application
MCA Academic Mini-Project
Backend: Python Flask
Database: MongoDB (PyMongo) with MongoDB Atlas & embedded fallback
"""

import os
from datetime import datetime, date
from flask import (
    Flask, render_template, request, redirect, url_for,
    flash, session, jsonify, abort
)
from werkzeug.utils import secure_filename

from config import Config
import db
from db import get_db, get_db_status, to_object_id, serialize_doc, serialize_docs
from services.auth_service import (
    register_user, authenticate_user, set_user_session, clear_user_session,
    get_current_user, login_required, admin_required, update_user_profile,
    change_user_password
)
from services.matcher import find_matches_for_item, get_smart_alerts_for_user
from services.stats_service import (
    get_platform_statistics, get_category_distribution,
    get_recent_activity_logs, log_activity, get_user_dashboard_stats
)

app = Flask(__name__)
app.config.from_object(Config)

# Ensure upload directory exists
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in Config.ALLOWED_EXTENSIONS

# Global context processors for templates
@app.context_processor
def inject_globals():
    return {
        'categories': Config.CATEGORIES,
        'db_status': get_db_status(),
        'current_year': datetime.now().year,
        'today': date.today().strftime('%Y-%m-%d')
    }

# ============================================================================
# 1. HOME & PUBLIC VIEWS
# ============================================================================

@app.route('/')
def index():
    """1. Home Page with hero, live statistics, recent items and categories."""
    database = get_db()
    stats = get_platform_statistics()
    recent_items = serialize_docs(
        list(database.items.find().sort("created_at", -1).limit(6))
    )
    return render_template('index.html', stats=stats, recent_items=recent_items)

# ============================================================================
# 2 & 3. AUTHENTICATION (REGISTER & LOGIN)
# ============================================================================

@app.route('/register', methods=['GET', 'POST'])
def register():
    """2. User Registration."""
    if session.get('user_id'):
        return redirect(url_for('dashboard'))
        
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        email = request.form.get('email', '').strip()
        phone = request.form.get('phone', '').strip()
        campus = request.form.get('campus', '').strip()
        password = request.form.get('password', '')
        confirm_password = request.form.get('confirm_password', '')
        
        if not name or not email or not phone or not password:
            flash('All required fields must be filled.', 'danger')
            return render_template('register.html')
            
        if password != confirm_password:
            flash('Passwords do not match. Please verify.', 'danger')
            return render_template('register.html')
            
        success, result = register_user(
            name=name,
            email=email,
            phone=phone,
            password=password,
            campus=campus or "Main Campus",
            role="user"
        )
        
        if success:
            set_user_session(result)
            log_activity("User Registered", f"New account created for {name}", user_name=name)
            flash(f'Welcome to LOSTLINK, {name}! Your account has been created.', 'success')
            return redirect(url_for('dashboard'))
        else:
            flash(result, 'danger')
            
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    """3. User Login."""
    if session.get('user_id'):
        return redirect(url_for('dashboard'))
        
    next_page = request.args.get('next')
    
    if request.method == 'POST':
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '')
        
        if not email or not password:
            flash('Please enter both email and password.', 'warning')
            return render_template('login.html')
            
        success, user = authenticate_user(email, password)
        if success:
            set_user_session(user)
            log_activity("User Login", f"{user.get('name')} signed in", user_name=user.get('name'))
            flash(f"Welcome back, {user.get('name')}!", 'success')
            if next_page and next_page.startswith('/'):
                return redirect(next_page)
            if user.get('role') == 'admin':
                return redirect(url_for('admin'))
            return redirect(url_for('dashboard'))
        else:
            flash(user, 'danger')
            
    return render_template('login.html')

@app.route('/logout')
def logout():
    """Sign out user and clear session."""
    user_name = session.get('user_name', 'User')
    clear_user_session()
    flash(f"Goodbye {user_name}, you have been signed out.", "info")
    return redirect(url_for('index'))

# ============================================================================
# 4. USER DASHBOARD
# ============================================================================

@app.route('/dashboard')
@login_required
def dashboard():
    """4. User Dashboard with metrics, smart alerts, and reports overview."""
    user = get_current_user()
    if not user:
        return redirect(url_for('login'))
        
    user_id = str(user['_id'])
    user_stats = get_user_dashboard_stats(user_id)
    smart_alerts = get_smart_alerts_for_user(user_id, limit=4)
    
    database = get_db()
    recent_user_items = serialize_docs(
        list(database.items.find({"reporter_id": user_id}).sort("created_at", -1).limit(5))
    )
    recent_activities = get_recent_activity_logs(limit=6)
    
    return render_template(
        'dashboard.html',
        user=user,
        user_stats=user_stats,
        smart_alerts=smart_alerts,
        recent_user_items=recent_user_items,
        recent_activities=recent_activities
    )

# ============================================================================
# 5 & 6. REPORTING (LOST & FOUND ITEMS)
# ============================================================================

@app.route('/report-lost', methods=['GET', 'POST'])
@login_required
def report_lost():
    """5. Report a Lost Item."""
    user = get_current_user()
    
    if request.method == 'POST':
        title = request.form.get('title', '').strip()
        category = request.form.get('category', '').strip()
        brand = request.form.get('brand', '').strip()
        color = request.form.get('color', '').strip()
        date_lost = request.form.get('date_lost', '').strip()
        location = request.form.get('location', '').strip()
        description = request.form.get('description', '').strip()
        reward = request.form.get('reward', '').strip()
        contact_method = request.form.get('contact_method', 'In-App Claims')
        
        if not title or not category or not location or not description:
            flash('Please complete all required fields.', 'danger')
            return render_template('report_lost.html')
            
        # Handle file upload
        image_url = None
        if 'image' in request.files:
            file = request.files['image']
            if file and file.filename and allowed_file(file.filename):
                filename = secure_filename(f"lost_{int(datetime.now().timestamp())}_{file.filename}")
                filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                file.save(filepath)
                image_url = url_for('static', filename=f'uploads/{filename}')
                
        database = get_db()
        item_doc = {
            "type": "lost",
            "title": title,
            "category": category,
            "brand": brand,
            "color": color,
            "date_lost": date_lost or date.today().strftime('%Y-%m-%d'),
            "location": location,
            "description": description,
            "reward": reward,
            "contact_method": contact_method,
            "image_url": image_url,
            "status": "Lost",
            "reporter_id": str(user['_id']),
            "reporter_name": user.get('name'),
            "reporter_email": user.get('email'),
            "reporter_phone": user.get('phone'),
            "created_at": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            "inquiries": []
        }
        
        res = database.items.insert_one(item_doc)
        item_id = str(res.inserted_id)
        
        log_activity("Lost Item Reported", f"'{title}' reported lost at {location}", user_name=user.get('name'), item_id=item_id, item_title=title)
        flash('Your lost item report has been published successfully!', 'success')
        return redirect(url_for('item_detail', item_id=item_id))
        
    return render_template('report_lost.html')

@app.route('/report-found', methods=['GET', 'POST'])
@login_required
def report_found():
    """6. Report a Found Item."""
    user = get_current_user()
    
    if request.method == 'POST':
        title = request.form.get('title', '').strip()
        category = request.form.get('category', '').strip()
        brand = request.form.get('brand', '').strip()
        color = request.form.get('color', '').strip()
        date_found = request.form.get('date_found', '').strip()
        location = request.form.get('location', '').strip()
        storage_location = request.form.get('storage_location', '').strip()
        description = request.form.get('description', '').strip()
        
        if not title or not category or not location or not description:
            flash('Please complete all required fields.', 'danger')
            return render_template('report_found.html')
            
        # Handle file upload
        image_url = None
        if 'image' in request.files:
            file = request.files['image']
            if file and file.filename and allowed_file(file.filename):
                filename = secure_filename(f"found_{int(datetime.now().timestamp())}_{file.filename}")
                filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                file.save(filepath)
                image_url = url_for('static', filename=f'uploads/{filename}')
                
        database = get_db()
        item_doc = {
            "type": "found",
            "title": title,
            "category": category,
            "brand": brand,
            "color": color,
            "date_found": date_found or date.today().strftime('%Y-%m-%d'),
            "location": location,
            "storage_location": storage_location or "With Finder",
            "description": description,
            "image_url": image_url,
            "status": "Available",
            "reporter_id": str(user['_id']),
            "reporter_name": user.get('name'),
            "reporter_email": user.get('email'),
            "reporter_phone": user.get('phone'),
            "created_at": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            "inquiries": []
        }
        
        res = database.items.insert_one(item_doc)
        item_id = str(res.inserted_id)
        
        log_activity("Found Item Reported", f"'{title}' found at {location}", user_name=user.get('name'), item_id=item_id, item_title=title)
        flash('Thank you! Your found item report has been registered.', 'success')
        return redirect(url_for('item_detail', item_id=item_id))
        
    return render_template('report_found.html')

# ============================================================================
# 7. SEARCH & BROWSE ITEMS
# ============================================================================

@app.route('/items')
def items():
    """7. Search & Browse items with multi-factor filters."""
    database = get_db()
    
    search_q = request.args.get('q', '').strip()
    item_type = request.args.get('type', 'all').lower()
    category = request.args.get('category', 'all').lower()
    location = request.args.get('location', '').strip()
    
    query = {}
    if item_type in ['lost', 'found']:
        query['type'] = item_type
        
    if category and category != 'all':
        query['category'] = category
        
    if location:
        query['location'] = {'$regex': location, '$options': 'i'}
        
    if search_q:
        query['$or'] = [
            {'title': {'$regex': search_q, '$options': 'i'}},
            {'description': {'$regex': search_q, '$options': 'i'}},
            {'brand': {'$regex': search_q, '$options': 'i'}},
            {'location': {'$regex': search_q, '$options': 'i'}}
        ]
        
    item_list = serialize_docs(
        list(database.items.find(query).sort("created_at", -1))
    )
    
    return render_template(
        'items.html',
        items=item_list,
        search_query=search_q,
        current_type=item_type,
        current_category=category
    )

# ============================================================================
# 8. ITEM DETAILS & MATCHES
# ============================================================================

@app.route('/item/<item_id>')
def item_detail(item_id):
    """8. Detailed item view with AI Smart Matches and Claim modal."""
    database = get_db()
    item = database.items.find_one({"_id": to_object_id(item_id)})
    if not item:
        flash("Item not found.", "danger")
        return redirect(url_for('items'))
        
    item_serialized = serialize_doc(item)
    # Compute counterpart matches using the Smart Matching Algorithm
    matches = find_matches_for_item(item_id, limit=4, min_score=35)
    
    return render_template('item_detail.html', item=item_serialized, matches=matches)

@app.route('/item/<item_id>/flyer')
def printable_flyer(item_id):
    """Bonus: Generate printable Lost/Found notice poster."""
    database = get_db()
    item = database.items.find_one({"_id": to_object_id(item_id)})
    if not item:
        abort(404)
    return render_template('printable_flyer.html', item=serialize_doc(item))

@app.route('/item/<item_id>/inquiry', methods=['POST'])
@login_required
def post_inquiry(item_id):
    """Post a public inquiry/question on an item."""
    database = get_db()
    item = database.items.find_one({"_id": to_object_id(item_id)})
    if not item:
        abort(404)
        
    message = request.form.get('message', '').strip()
    if message:
        user = get_current_user()
        inquiry_obj = {
            "author_id": str(user['_id']),
            "author_name": user.get('name'),
            "message": message,
            "timestamp": datetime.now().strftime('%Y-%m-%d %H:%M')
        }
        database.items.update_one(
            {"_id": to_object_id(item_id)},
            {"$push": {"inquiries": inquiry_obj}}
        )
        flash('Inquiry message posted successfully.', 'success')
    return redirect(url_for('item_detail', item_id=item_id))

# ============================================================================
# 9. MY REPORTS
# ============================================================================

@app.route('/my-reports')
@login_required
def my_reports():
    """9. View personal reported lost and found items."""
    database = get_db()
    user_id = session.get('user_id')
    
    lost_items = serialize_docs(
        list(database.items.find({"reporter_id": user_id, "type": "lost"}).sort("created_at", -1))
    )
    found_items = serialize_docs(
        list(database.items.find({"reporter_id": user_id, "type": "found"}).sort("created_at", -1))
    )
    
    return render_template('my_reports.html', lost_items=lost_items, found_items=found_items)

@app.route('/item/<item_id>/recovered', methods=['POST'])
@login_required
def mark_recovered(item_id):
    """Mark an item as recovered / returned."""
    database = get_db()
    item = database.items.find_one({"_id": to_object_id(item_id)})
    if not item:
        abort(404)
        
    new_status = "Recovered" if item.get("type") == "lost" else "Returned to Owner"
    database.items.update_one(
        {"_id": to_object_id(item_id)},
        {"$set": {"status": new_status, "resolved_at": datetime.now().strftime('%Y-%m-%d %H:%M:%S')}}
    )
    
    log_activity("Item Solved", f"'{item.get('title')}' was marked as {new_status}", user_name=session.get('user_name'))
    flash(f"Item status updated to '{new_status}'. Congratulations!", "success")
    return redirect(request.referrer or url_for('my_reports'))

@app.route('/item/<item_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_item(item_id):
    """Edit an existing report."""
    database = get_db()
    item = database.items.find_one({"_id": to_object_id(item_id)})
    if not item:
        abort(404)
        
    user_id = session.get('user_id')
    user_role = session.get('user_role')
    if item.get("reporter_id") != user_id and user_role != "admin":
        flash("You do not have permission to edit this report.", "danger")
        return redirect(url_for('items'))
        
    if request.method == 'POST':
        title = request.form.get('title', '').strip()
        category = request.form.get('category', '').strip()
        brand = request.form.get('brand', '').strip()
        color = request.form.get('color', '').strip()
        location = request.form.get('location', '').strip()
        description = request.form.get('description', '').strip()
        status = request.form.get('status', '').strip()
        
        database.items.update_one(
            {"_id": to_object_id(item_id)},
            {"$set": {
                "title": title,
                "category": category,
                "brand": brand,
                "color": color,
                "location": location,
                "description": description,
                "status": status,
                "updated_at": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }}
        )
        flash("Item report updated successfully.", "success")
        return redirect(url_for('item_detail', item_id=item_id))
        
    return render_template('edit_item.html', item=serialize_doc(item))

@app.route('/item/<item_id>/delete', methods=['POST'])
@login_required
def delete_item(item_id):
    """Delete an item report."""
    database = get_db()
    item = database.items.find_one({"_id": to_object_id(item_id)})
    if not item:
        abort(404)
        
    user_id = session.get('user_id')
    user_role = session.get('user_role')
    if item.get("reporter_id") != user_id and user_role != "admin":
        flash("You do not have permission to delete this report.", "danger")
        return redirect(url_for('items'))
        
    database.items.delete_one({"_id": to_object_id(item_id)})
    # Also delete associated claims
    database.claims.delete_many({"item_id": str(item_id)})
    
    log_activity("Item Deleted", f"'{item.get('title')}' was removed", user_name=session.get('user_name'))
    flash("Item report was deleted.", "info")
    return redirect(request.referrer or url_for('my_reports'))

# ============================================================================
# 10. CLAIM MANAGEMENT
# ============================================================================

@app.route('/claims')
@login_required
def claims():
    """10. Claims dashboard: incoming and outgoing claims."""
    database = get_db()
    user_id = session.get('user_id')
    
    # 1. Claims submitted by current user
    claims_submitted = serialize_docs(
        list(database.claims.find({"claimant_id": user_id}).sort("created_at", -1))
    )
    
    # 2. Claims received on items reported by current user
    my_found_items = list(database.items.find({"reporter_id": user_id, "type": "found"}))
    my_found_ids = [str(itm['_id']) for itm in my_found_items]
    
    claims_received = []
    if my_found_ids:
        claims_received = serialize_docs(
            list(database.claims.find({"item_id": {"$in": my_found_ids}}).sort("created_at", -1))
        )
        
    return render_template(
        'claims.html',
        claims_submitted=claims_submitted,
        claims_received=claims_received
    )

@app.route('/item/<item_id>/claim', methods=['POST'])
@login_required
def submit_claim(item_id):
    """Submit an ownership verification claim on a found item."""
    database = get_db()
    item = database.items.find_one({"_id": to_object_id(item_id)})
    if not item:
        abort(404)
        
    user = get_current_user()
    user_id = str(user['_id'])
    
    if item.get("reporter_id") == user_id:
        flash("You cannot file a claim on an item you reported yourself.", "warning")
        return redirect(url_for('item_detail', item_id=item_id))
        
    proof_description = request.form.get('proof_description', '').strip()
    contact_phone = request.form.get('contact_phone', '').strip()
    preferred_location = request.form.get('preferred_location', '').strip()
    
    if not proof_description or not contact_phone:
        flash("Please provide detailed proof and a contact phone number.", "danger")
        return redirect(url_for('item_detail', item_id=item_id))
        
    # Handle proof file upload
    proof_file_url = None
    if 'proof_file' in request.files:
        file = request.files['proof_file']
        if file and file.filename and allowed_file(file.filename):
            filename = secure_filename(f"proof_{int(datetime.now().timestamp())}_{file.filename}")
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(filepath)
            proof_file_url = url_for('static', filename=f'uploads/{filename}')
            
    claim_doc = {
        "item_id": str(item_id),
        "item_title": item.get('title'),
        "item_type": item.get('type'),
        "finder_id": item.get('reporter_id'),
        "claimant_id": user_id,
        "claimant_name": user.get('name'),
        "claimant_email": user.get('email'),
        "contact_phone": contact_phone,
        "proof_description": proof_description,
        "proof_file_url": proof_file_url,
        "preferred_location": preferred_location,
        "status": "Pending",
        "created_at": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    }
    
    database.claims.insert_one(claim_doc)
    
    # Update item status to 'Claim Pending' if available
    if item.get("status") in ["Available", "Lost"]:
        new_status = "Claim Pending" if item.get("type") == "found" else "Under Claim"
        database.items.update_one({"_id": to_object_id(item_id)}, {"$set": {"status": new_status}})
        
    log_activity("Claim Submitted", f"{user.get('name')} submitted claim on '{item.get('title')}'", user_name=user.get('name'), item_id=item_id)
    flash("Your claim request has been submitted for verification. Track it under Claim Requests.", "success")
    return redirect(url_for('claims'))

@app.route('/claim/<claim_id>/approve', methods=['POST'])
@login_required
def approve_claim(claim_id):
    """Approve a claim request."""
    database = get_db()
    claim = database.claims.find_one({"_id": to_object_id(claim_id)})
    if not claim:
        abort(404)
        
    user_id = session.get('user_id')
    user_role = session.get('user_role')
    
    # Can only be approved by finder or admin
    if claim.get("finder_id") != user_id and user_role != "admin":
        flash("You do not have authorization to approve this claim.", "danger")
        return redirect(url_for('claims'))
        
    # Update claim
    database.claims.update_one(
        {"_id": to_object_id(claim_id)},
        {"$set": {"status": "Approved", "resolved_at": datetime.now().strftime('%Y-%m-%d %H:%M:%S')}}
    )
    
    # Update item to 'Returned to Owner' / 'Recovered'
    target_item_id = claim.get("item_id")
    if target_item_id:
        database.items.update_one(
            {"_id": to_object_id(target_item_id)},
            {"$set": {"status": "Returned to Owner", "resolved_at": datetime.now().strftime('%Y-%m-%d %H:%M:%S')}}
        )
        
    log_activity("Claim Approved", f"Claim approved for '{claim.get('item_title')}'. Item returned to {claim.get('claimant_name')}.", user_name=session.get('user_name'))
    flash("Claim approved! The owner has been verified.", "success")
    return redirect(request.referrer or url_for('claims'))

@app.route('/claim/<claim_id>/reject', methods=['POST'])
@login_required
def reject_claim(claim_id):
    """Reject a claim request."""
    database = get_db()
    claim = database.claims.find_one({"_id": to_object_id(claim_id)})
    if not claim:
        abort(404)
        
    user_id = session.get('user_id')
    user_role = session.get('user_role')
    
    if claim.get("finder_id") != user_id and user_role != "admin":
        flash("You do not have authorization to decide this claim.", "danger")
        return redirect(url_for('claims'))
        
    database.claims.update_one(
        {"_id": to_object_id(claim_id)},
        {"$set": {"status": "Rejected", "resolved_at": datetime.now().strftime('%Y-%m-%d %H:%M:%S')}}
    )
    
    # If no other pending claims, reset item status to Available
    target_item_id = claim.get("item_id")
    if target_item_id:
        other_pending = database.claims.count_documents({"item_id": target_item_id, "status": "Pending"})
        if other_pending == 0:
            database.items.update_one(
                {"_id": to_object_id(target_item_id)},
                {"$set": {"status": "Available"}}
            )
            
    log_activity("Claim Rejected", f"Claim rejected for '{claim.get('item_title')}'", user_name=session.get('user_name'))
    flash("Claim has been rejected.", "info")
    return redirect(request.referrer or url_for('claims'))

# ============================================================================
# 11. USER PROFILE
# ============================================================================

@app.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    """11. User Profile and password update."""
    user = get_current_user()
    
    if request.method == 'POST':
        form_type = request.form.get('form_type')
        
        if form_type == 'profile':
            name = request.form.get('name', '').strip()
            phone = request.form.get('phone', '').strip()
            campus = request.form.get('campus', '').strip()
            bio = request.form.get('bio', '').strip()
            
            if not name or not phone:
                flash("Name and phone number cannot be empty.", "danger")
            else:
                update_user_profile(user['_id'], name, phone, campus, bio)
                flash("Profile details updated successfully.", "success")
                return redirect(url_for('profile'))
                
        elif form_type == 'password':
            old_password = request.form.get('old_password', '')
            new_password = request.form.get('new_password', '')
            confirm_new = request.form.get('confirm_new_password', '')
            
            if new_password != confirm_new:
                flash("New passwords do not match.", "danger")
            else:
                ok, msg = change_user_password(user['_id'], old_password, new_password)
                if ok:
                    flash(msg, "success")
                else:
                    flash(msg, "danger")
            return redirect(url_for('profile'))
            
    return render_template('profile.html', user=user)

# ============================================================================
# 12. ADMIN DASHBOARD
# ============================================================================

@app.route('/admin')
@admin_required
def admin():
    """12. Admin Dashboard with moderation queue, platform stats, charts, and users."""
    database = get_db()
    stats = get_platform_statistics()
    category_chart_data = get_category_distribution()
    
    claims_list = serialize_docs(
        list(database.claims.find().sort("created_at", -1))
    )
    all_items = serialize_docs(
        list(database.items.find().sort("created_at", -1))
    )
    all_users = serialize_docs(
        list(database.users.find().sort("created_at", -1))
    )
    
    return render_template(
        'admin.html',
        stats=stats,
        category_chart_data=category_chart_data,
        claims=claims_list,
        all_items=all_items,
        all_users=all_users
    )

@app.route('/admin/user/<user_id>/toggle-role', methods=['POST'])
@admin_required
def admin_toggle_role(user_id):
    """Toggle user role between 'user' and 'admin'."""
    database = get_db()
    user = database.users.find_one({"_id": to_object_id(user_id)})
    if not user:
        abort(404)
        
    new_role = "admin" if user.get("role") != "admin" else "user"
    database.users.update_one({"_id": to_object_id(user_id)}, {"$set": {"role": new_role}})
    flash(f"User {user.get('name')} role updated to '{new_role}'.", "success")
    return redirect(url_for('admin'))

# ============================================================================
# API ENDPOINT FOR SMART MATCHING
# ============================================================================

@app.route('/api/matches/<item_id>')
def api_matches(item_id):
    """API endpoint to get algorithmic matches for an item in JSON format."""
    matches = find_matches_for_item(item_id)
    return jsonify({"success": True, "item_id": item_id, "matches": matches})

# Error Handlers
@app.errorhandler(404)
def not_found(e):
    return render_template('404.html'), 404

@app.errorhandler(500)
def server_error(e):
    return "<h3>Internal Server Error (500)</h3><p>An unexpected error occurred.</p>", 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    print(f"==================================================")
    print(f"🚀 LOSTLINK Platform Starting on http://127.0.0.1:{port}")
    print(f"Database Mode: {get_db_status()['status_message']}")
    print(f"==================================================")
    app.run(host='0.0.0.0', port=port, debug=True)
