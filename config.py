import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class Config:
    SECRET_KEY = os.getenv('SECRET_KEY', 'lostlink-default-mca-secret-key-98765')
    MONGODB_URI = os.getenv('MONGODB_URI', '')
    DB_NAME = os.getenv('DB_NAME', 'lostlink_db')
    
    # Uploads configuration
    BASE_DIR = os.path.abspath(os.path.dirname(__file__))
    UPLOAD_FOLDER = os.path.join(BASE_DIR, 'static', 'uploads')
    MAX_CONTENT_LENGTH = int(os.getenv('MAX_CONTENT_LENGTH', 16 * 1024 * 1024)) # 16 MB
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
    
    # Categories for items
    CATEGORIES = [
        {"id": "electronics", "name": "Electronics & Gadgets", "icon": "fa-laptop", "color": "#4f46e5"},
        {"id": "wallets_bags", "name": "Wallets, Bags & Backpacks", "icon": "fa-wallet", "color": "#0ea5e9"},
        {"id": "ids_cards", "name": "ID Cards & Documents", "icon": "fa-id-card", "color": "#f59e0b"},
        {"id": "keys", "name": "Keys & Access Cards", "icon": "fa-key", "color": "#10b981"},
        {"id": "jewels_watches", "name": "Jewelry & Watches", "icon": "fa-ring", "color": "#ec4899"},
        {"id": "books_stationery", "name": "Books & Stationery", "icon": "fa-book", "color": "#8b5cf6"},
        {"id": "clothing_accessories", "name": "Clothing & Accessories", "icon": "fa-shirt", "color": "#06b6d4"},
        {"id": "mobile_phones", "name": "Smartphones & Tablets", "icon": "fa-mobile-screen-button", "color": "#f97316"},
        {"id": "vehicles", "name": "Bicycles & Vehicles", "icon": "fa-bicycle", "color": "#14b8a6"},
        {"id": "others", "name": "Others & Miscellaneous", "icon": "fa-box-open", "color": "#64748b"}
    ]
    
    # Status options
    LOST_STATUSES = ["Lost", "Under Claim", "Recovered", "Closed"]
    FOUND_STATUSES = ["Available", "Claim Pending", "Returned to Owner", "Archived"]
    CLAIM_STATUSES = ["Pending", "Under Review", "Approved", "Rejected"]
