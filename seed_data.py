"""
LOSTLINK - Database Seeder Script
Populates realistic users, lost & found reports, smart matching pairs,
claims, and audit logs for MCA project demonstration and viva evaluation.
"""

from datetime import datetime, timedelta
from werkzeug.security import generate_password_hash
from db import get_db, serialize_doc

def seed_database():
    database = get_db()
    print("Clearing existing sample records for fresh seed...")
    
    # In embedded or Atlas database, reset items and users if needed
    if hasattr(database, 'data'):
        database.data = {"users": [], "items": [], "claims": [], "activity_logs": [], "categories": []}
        database._save_data()
    else:
        database.users.delete_many({})
        database.items.delete_many({})
        database.claims.delete_many({})
        database.activity_logs.delete_many({})

    print("Seeding Users...")
    now = datetime.now()
    
    users_data = [
        {
            "name": "Dr. Arvind Rao",
            "email": "admin@lostlink.com",
            "phone": "9845012345",
            "campus": "Department of MCA - HOD Office",
            "password": generate_password_hash("admin123"),
            "role": "admin",
            "avatar": "https://api.dicebear.com/7.x/identicon/svg?seed=arvind_admin",
            "created_at": (now - timedelta(days=60)).strftime("%Y-%m-%d %H:%M:%S"),
            "is_active": True,
            "reputation_score": 500
        },
        {
            "name": "Rahul Sharma",
            "email": "rahul@lostlink.com",
            "phone": "9876543210",
            "campus": "MCA Final Year (Roll: MCA2024-042)",
            "password": generate_password_hash("user123"),
            "role": "user",
            "avatar": "https://api.dicebear.com/7.x/identicon/svg?seed=rahul_student",
            "created_at": (now - timedelta(days=30)).strftime("%Y-%m-%d %H:%M:%S"),
            "is_active": True,
            "reputation_score": 120
        },
        {
            "name": "Priya Patel",
            "email": "priya@lostlink.com",
            "phone": "9123456780",
            "campus": "CSE Block B, 3rd Sem",
            "password": generate_password_hash("user123"),
            "role": "user",
            "avatar": "https://api.dicebear.com/7.x/identicon/svg?seed=priya_patel",
            "created_at": (now - timedelta(days=25)).strftime("%Y-%m-%d %H:%M:%S"),
            "is_active": True,
            "reputation_score": 180
        },
        {
            "name": "Ramesh Kumar (Security)",
            "email": "security@lostlink.com",
            "phone": "9880011223",
            "campus": "Central Campus Security Gate 1",
            "password": generate_password_hash("user123"),
            "role": "user",
            "avatar": "https://api.dicebear.com/7.x/identicon/svg?seed=ramesh_security",
            "created_at": (now - timedelta(days=45)).strftime("%Y-%m-%d %H:%M:%S"),
            "is_active": True,
            "reputation_score": 350
        }
    ]

    user_map = {}
    for u in users_data:
        res = database.users.insert_one(u)
        user_map[u["email"]] = str(res.inserted_id)
        print(f"  + Added user: {u['name']} ({u['email']}) [Role: {u['role']}]")

    print("\nSeeding Lost and Found Items (including Smart Match pairs)...")
    
    items_data = [
        # Pair 1: High Match - Dell XPS Laptop (Lost & Found counterpart)
        {
            "type": "lost",
            "title": "Dell XPS 15 9520 Laptop",
            "category": "electronics",
            "brand": "Dell",
            "color": "Matte Black",
            "date_lost": (now - timedelta(days=4)).strftime("%Y-%m-%d"),
            "location": "Central Library 2nd Floor Study Room",
            "description": "High-end developer laptop with black carbon fiber interior. Has a bright blue Python logo sticker and GitHub octocat decal on the top lid. Crucial project code stored inside.",
            "reward": "1500",
            "contact_method": "In-App Claims & Phone",
            "image_url": "https://images.unsplash.com/photo-1593642632823-8f785ba67e45?w=600&auto=format&fit=crop&q=80",
            "status": "Lost",
            "reporter_id": user_map["rahul@lostlink.com"],
            "reporter_name": "Rahul Sharma",
            "reporter_email": "rahul@lostlink.com",
            "reporter_phone": "9876543210",
            "created_at": (now - timedelta(days=4)).strftime("%Y-%m-%d 14:30:00"),
            "inquiries": [
                {
                    "author_name": "Priya Patel",
                    "message": "Did it have a blue laptop sleeve or charger left with it?",
                    "timestamp": (now - timedelta(days=3)).strftime("%Y-%m-%d 16:10")
                }
            ]
        },
        {
            "type": "found",
            "title": "Dell XPS Laptop Black with Decals",
            "category": "electronics",
            "brand": "Dell",
            "color": "Black",
            "date_found": (now - timedelta(days=3)).strftime("%Y-%m-%d"),
            "location": "Central Library 2nd Floor Study Desk near Window",
            "storage_location": "Deposited safely at Central Library Helpdesk with Librarian Mrs. Sheela",
            "description": "Found a premium black Dell laptop left unattended on study desk #14 after closing hours. Noticeable programming stickers on back. Kept safe under lock.",
            "image_url": "https://images.unsplash.com/photo-1588872657578-7efd1f1555ed?w=600&auto=format&fit=crop&q=80",
            "status": "Available",
            "reporter_id": user_map["security@lostlink.com"],
            "reporter_name": "Ramesh Kumar (Security)",
            "reporter_email": "security@lostlink.com",
            "reporter_phone": "9880011223",
            "created_at": (now - timedelta(days=3)).strftime("%Y-%m-%d 19:45:00"),
            "inquiries": []
        },

        # Pair 2: Wildhorn Brown Leather Wallet (Lost & Found counterpart with pending claim)
        {
            "type": "lost",
            "title": "Wildhorn Leather Bi-fold Brown Wallet",
            "category": "wallets_bags",
            "brand": "Wildhorn",
            "color": "Dark Brown",
            "date_lost": (now - timedelta(days=6)).strftime("%Y-%m-%d"),
            "location": "Campus Cafeteria Main Dining Hall",
            "description": "Genuine brown leather wallet with embossed Wildhorn logo. Contains college library card, driving license, and debit card.",
            "reward": "500",
            "contact_method": "In-App Claims",
            "image_url": "https://images.unsplash.com/photo-1627123424574-724758594e93?w=600&auto=format&fit=crop&q=80",
            "status": "Under Claim",
            "reporter_id": user_map["rahul@lostlink.com"],
            "reporter_name": "Rahul Sharma",
            "reporter_email": "rahul@lostlink.com",
            "reporter_phone": "9876543210",
            "created_at": (now - timedelta(days=6)).strftime("%Y-%m-%d 13:15:00"),
            "inquiries": []
        },
        {
            "type": "found",
            "title": "Brown Leather Wallet with ID Cards",
            "category": "wallets_bags",
            "brand": "Wildhorn",
            "color": "Brown",
            "date_found": (now - timedelta(days=5)).strftime("%Y-%m-%d"),
            "location": "Cafeteria Table #8 near Water Counter",
            "storage_location": "Kept in security vault at Campus Gate 1 Office",
            "description": "Found dark brown gent's wallet containing cash and identity documents. Owner must declare the exact name and details on the ID to claim.",
            "image_url": "https://images.unsplash.com/photo-1559563458-527698bf5295?w=600&auto=format&fit=crop&q=80",
            "status": "Claim Pending",
            "reporter_id": user_map["priya@lostlink.com"],
            "reporter_name": "Priya Patel",
            "reporter_email": "priya@lostlink.com",
            "reporter_phone": "9123456780",
            "created_at": (now - timedelta(days=5)).strftime("%Y-%m-%d 14:00:00"),
            "inquiries": []
        },

        # Pair 3: Apple iPhone 14 Midnight Blue
        {
            "type": "lost",
            "title": "Apple iPhone 14 128GB Midnight Blue",
            "category": "mobile_phones",
            "brand": "Apple",
            "color": "Midnight Blue",
            "date_lost": (now - timedelta(days=2)).strftime("%Y-%m-%d"),
            "location": "Sports Ground Basketball Court",
            "description": "Slipped out of gym shorts during evening practice. Midnight blue color, black silicone case, lock screen has a picture of a Golden Retriever.",
            "reward": "2000",
            "contact_method": "Phone Number",
            "image_url": "https://images.unsplash.com/photo-1510557880182-3d4d3cba35a5?w=600&auto=format&fit=crop&q=80",
            "status": "Lost",
            "reporter_id": user_map["priya@lostlink.com"],
            "reporter_name": "Priya Patel",
            "reporter_email": "priya@lostlink.com",
            "reporter_phone": "9123456780",
            "created_at": (now - timedelta(days=2)).strftime("%Y-%m-%d 18:20:00"),
            "inquiries": []
        },
        {
            "type": "found",
            "title": "Blue Apple iPhone with Dog Wallpaper",
            "category": "mobile_phones",
            "brand": "Apple",
            "color": "Blue",
            "date_found": (now - timedelta(days=1)).strftime("%Y-%m-%d"),
            "location": "Sports Ground Pavilion Bleachers",
            "storage_location": "With Physical Education Director Room #102",
            "description": "Found an iPhone on the wooden bleachers. Screen turns on showing dog wallpaper. Charged to 60%. Please unlock with passcode to verify.",
            "image_url": "https://images.unsplash.com/photo-1592750475338-74b7b21085ab?w=600&auto=format&fit=crop&q=80",
            "status": "Available",
            "reporter_id": user_map["security@lostlink.com"],
            "reporter_name": "Ramesh Kumar (Security)",
            "reporter_email": "security@lostlink.com",
            "reporter_phone": "9880011223",
            "created_at": (now - timedelta(days=1)).strftime("%Y-%m-%d 09:10:00"),
            "inquiries": []
        },

        # Item 7: Recovered Success Story
        {
            "type": "lost",
            "title": "Hero Sprint Pro 21-Speed Mountain Bicycle",
            "category": "vehicles",
            "brand": "Hero",
            "color": "Matte Green and Black",
            "date_lost": (now - timedelta(days=14)).strftime("%Y-%m-%d"),
            "location": "Cycle Stand adjacent to MCA Block",
            "description": "Geared cycle with front suspension and water bottle holder. Has small college parking token tag #B-108.",
            "reward": "500",
            "contact_method": "In-App Claims",
            "image_url": "https://images.unsplash.com/photo-1485965120184-e220f721d03e?w=600&auto=format&fit=crop&q=80",
            "status": "Recovered",
            "reporter_id": user_map["rahul@lostlink.com"],
            "reporter_name": "Rahul Sharma",
            "reporter_email": "rahul@lostlink.com",
            "reporter_phone": "9876543210",
            "created_at": (now - timedelta(days=14)).strftime("%Y-%m-%d 10:00:00"),
            "resolved_at": (now - timedelta(days=10)).strftime("%Y-%m-%d 17:30:00"),
            "inquiries": []
        },

        # Item 8: Found Titan Watch
        {
            "type": "found",
            "title": "Titan Octane Chronograph Wristwatch",
            "category": "jewels_watches",
            "brand": "Titan",
            "color": "Silver Metallic",
            "date_found": (now - timedelta(days=2)).strftime("%Y-%m-%d"),
            "location": "Main Auditorium Row F, Seat 12",
            "storage_location": "With Auditorium Coordinator Mr. Varma",
            "description": "Found immediately following the MCA Technical Symposium. Silver metal strap, dark blue dial with tachymeter.",
            "image_url": "https://images.unsplash.com/photo-1524805444758-089113d48a6d?w=600&auto=format&fit=crop&q=80",
            "status": "Available",
            "reporter_id": user_map["admin@lostlink.com"],
            "reporter_name": "Dr. Arvind Rao",
            "reporter_email": "admin@lostlink.com",
            "reporter_phone": "9845012345",
            "created_at": (now - timedelta(days=2)).strftime("%Y-%m-%d 17:00:00"),
            "inquiries": []
        },

        # Item 9: Lost University ID Card
        {
            "type": "lost",
            "title": "University Student RFID Smart Card",
            "category": "ids_cards",
            "brand": "University",
            "color": "Blue Lanyard",
            "date_lost": (now - timedelta(days=1)).strftime("%Y-%m-%d"),
            "location": "Computer Science Lab 3",
            "description": "Smart swipe card on blue MCA department ribbon lanyard. Needed urgently for semester lab entrance.",
            "reward": "200",
            "contact_method": "In-App Claims",
            "image_url": "https://images.unsplash.com/photo-1589829545856-d10d557cf95f?w=600&auto=format&fit=crop&q=80",
            "status": "Lost",
            "reporter_id": user_map["rahul@lostlink.com"],
            "reporter_name": "Rahul Sharma",
            "reporter_email": "rahul@lostlink.com",
            "reporter_phone": "9876543210",
            "created_at": (now - timedelta(days=1)).strftime("%Y-%m-%d 11:30:00"),
            "inquiries": []
        },

        # Item 10: Found Bunch of Keys
        {
            "type": "found",
            "title": "Bunch of 4 Godrej Cabinet Keys",
            "category": "keys",
            "brand": "Godrej",
            "color": "Brass and Silver",
            "date_found": now.strftime("%Y-%m-%d"),
            "location": "Faculty Staff Room Corridor 1st Floor",
            "storage_location": "Security Desk Gate 1",
            "description": "Ring of four keys with miniature metal Eiffel Tower keychain.",
            "image_url": "https://images.unsplash.com/photo-1582139329536-e7284fece509?w=600&auto=format&fit=crop&q=80",
            "status": "Available",
            "reporter_id": user_map["security@lostlink.com"],
            "reporter_name": "Ramesh Kumar (Security)",
            "reporter_email": "security@lostlink.com",
            "reporter_phone": "9880011223",
            "created_at": now.strftime("%Y-%m-%d 08:30:00"),
            "inquiries": []
        }
    ]

    item_ids = []
    for itm in items_data:
        res = database.items.insert_one(itm)
        item_ids.append(str(res.inserted_id))
        print(f"  + Added [{itm['type'].upper()}]: {itm['title']} ({itm['category']})")

    print("\nSeeding Ownership Claims...")
    # Seed a claim on Item 4 (Found Wildhorn wallet) submitted by Rahul Sharma
    found_wallet_id = item_ids[3]
    claim_1 = {
        "item_id": found_wallet_id,
        "item_title": "Brown Leather Wallet with ID Cards",
        "item_type": "found",
        "finder_id": user_map["priya@lostlink.com"],
        "claimant_id": user_map["rahul@lostlink.com"],
        "claimant_name": "Rahul Sharma",
        "claimant_email": "rahul@lostlink.com",
        "contact_phone": "9876543210",
        "proof_description": "My college ID card inside has Roll Number MCA2024-042 and my photo. There is also an emergency note tucked behind the currency flap.",
        "proof_file_url": None,
        "preferred_location": "Gate 1 Security Office or Cafeteria",
        "status": "Pending",
        "created_at": (now - timedelta(days=4)).strftime("%Y-%m-%d 15:20:00")
    }
    database.claims.insert_one(claim_1)
    print(f"  + Seeded Pending Claim on '{claim_1['item_title']}' by Rahul Sharma")

    # Seed an approved claim for Item 7
    recovered_bike_id = item_ids[6]
    claim_2 = {
        "item_id": recovered_bike_id,
        "item_title": "Hero Sprint Pro 21-Speed Mountain Bicycle",
        "item_type": "lost",
        "finder_id": user_map["security@lostlink.com"],
        "claimant_id": user_map["rahul@lostlink.com"],
        "claimant_name": "Rahul Sharma",
        "claimant_email": "rahul@lostlink.com",
        "contact_phone": "9876543210",
        "proof_description": "Original store purchase invoice and frame number matched with college security register.",
        "status": "Approved",
        "created_at": (now - timedelta(days=12)).strftime("%Y-%m-%d 11:00:00"),
        "resolved_at": (now - timedelta(days=10)).strftime("%Y-%m-%d 17:30:00")
    }
    database.claims.insert_one(claim_2)
    print(f"  + Seeded Approved Claim for '{claim_2['item_title']}'")

    print("\nSeeding Activity Logs...")
    logs = [
        ("Platform Initialized", "LOSTLINK MCA Mini-Project Database Engine started", "System", (now - timedelta(days=30))),
        ("Item Reported", "Dell XPS 15 9520 Laptop reported lost at Library", "Rahul Sharma", (now - timedelta(days=4))),
        ("Item Reported", "Dell XPS Laptop Black found at Library", "Ramesh Kumar (Security)", (now - timedelta(days=3))),
        ("Claim Submitted", "Rahul Sharma filed ownership claim for Brown Leather Wallet", "Rahul Sharma", (now - timedelta(days=4))),
        ("Item Solved", "Hero Sprint Pro Bicycle successfully reunited with verified owner", "Dr. Arvind Rao", (now - timedelta(days=10))),
        ("Item Reported", "Bunch of 4 Godrej Cabinet Keys reported found", "Ramesh Kumar (Security)", now)
    ]
    for action, desc, uname, dt in logs:
        database.activity_logs.insert_one({
            "action": action,
            "description": desc,
            "user_name": uname,
            "timestamp": dt.strftime("%Y-%m-%d %H:%M:%S")
        })
    print(f"  + Added {len(logs)} activity audit logs.")

    print("\n==================================================")
    print("✅ DATABASE SEEDING COMPLETED SUCCESSFULLY!")
    print("Demo Accounts:")
    print("  1. Admin:   admin@lostlink.com  | Password: admin123")
    print("  2. Student: rahul@lostlink.com  | Password: user123")
    print("  3. Student: priya@lostlink.com  | Password: user123")
    print("==================================================")

if __name__ == "__main__":
    seed_database()
