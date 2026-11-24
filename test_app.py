"""
LOSTLINK - Automated Test Suite
Verifies all 12 required pages, authentication flows, reporting,
smart matching algorithm, claims processing, and admin controls.
"""

import unittest
from app import app
import db

class LostLinkTestCase(unittest.TestCase):
    def setUp(self):
        app.config['TESTING'] = True
        app.config['WTF_CSRF_ENABLED'] = False
        self.client = app.test_client()

    # 1. Home Page Test
    def test_01_home_page(self):
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'LOSTLINK', response.data)
        self.assertIn(b"Lost Something? Let's Find It", response.data)
        self.assertIn(b'Total Lost Reports', response.data)
        print("✓ Page 1 (Home Page) passed.")

    # 2. Registration Page & Flow
    def test_02_registration_page_and_flow(self):
        # GET
        response = self.client.get('/register')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Create Your Account', response.data)
        
        # POST
        response = self.client.post('/register', data={
            'name': 'Test New Student',
            'email': 'newstudent@lostlink.com',
            'phone': '9988776655',
            'campus': 'MCA Block',
            'password': 'password123',
            'confirm_password': 'password123'
        }, follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Welcome to LOSTLINK', response.data)
        print("✓ Page 2 (User Registration) passed.")

    # 3. Login Page & Flow
    def test_03_login_page_and_flow(self):
        # GET
        response = self.client.get('/login')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Welcome Back', response.data)
        
        # POST student login
        response = self.client.post('/login', data={
            'email': 'rahul@lostlink.com',
            'password': 'user123'
        }, follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Welcome back', response.data)
        self.assertIn(b'Rahul', response.data)
        print("✓ Page 3 (User Login) passed.")

    # 4. User Dashboard
    def test_04_user_dashboard(self):
        with self.client:
            self.client.post('/login', data={'email': 'rahul@lostlink.com', 'password': 'user123'})
            response = self.client.get('/dashboard')
            self.assertEqual(response.status_code, 200)
            self.assertIn(b'Hello, Rahul', response.data)
            self.assertIn(b'Smart Match Alerts', response.data)
            self.assertIn(b'My Lost Items', response.data)
            print("✓ Page 4 (User Dashboard) passed.")

    # 5. Report Lost Item
    def test_05_report_lost_item(self):
        with self.client:
            self.client.post('/login', data={'email': 'rahul@lostlink.com', 'password': 'user123'})
            # GET
            response = self.client.get('/report-lost')
            self.assertEqual(response.status_code, 200)
            self.assertIn(b'Report a Lost Item', response.data)
            
            # POST
            response = self.client.post('/report-lost', data={
                'title': 'Sony WH-1000XM5 Headphones Silver',
                'category': 'electronics',
                'brand': 'Sony',
                'color': 'Silver',
                'date_lost': '2026-11-24',
                'location': 'Library 3rd Floor Quiet Zone',
                'description': 'Noise cancelling headphones in grey travel case.',
                'reward': '500',
                'contact_method': 'In-App Claims'
            }, follow_redirects=True)
            self.assertEqual(response.status_code, 200)
            self.assertIn(b'Sony WH-1000XM5', response.data)
            print("✓ Page 5 (Report Lost Item) passed.")

    # 6. Report Found Item
    def test_06_report_found_item(self):
        with self.client:
            self.client.post('/login', data={'email': 'priya@lostlink.com', 'password': 'user123'})
            # GET
            response = self.client.get('/report-found')
            self.assertEqual(response.status_code, 200)
            self.assertIn(b'Report a Found Item', response.data)
            
            # POST
            response = self.client.post('/report-found', data={
                'title': 'Sony Wireless Headphones Silver Case',
                'category': 'electronics',
                'brand': 'Sony',
                'color': 'Silver',
                'date_found': '2026-11-24',
                'location': 'Library 3rd Floor Desk',
                'storage_location': 'Left with Library Front Desk',
                'description': 'Found premium silver wireless headphones.'
            }, follow_redirects=True)
            self.assertEqual(response.status_code, 200)
            self.assertIn(b'Sony Wireless Headphones', response.data)
            print("✓ Page 6 (Report Found Item) passed.")

    # 7. Search Items
    def test_07_search_items(self):
        response = self.client.get('/items')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Browse Lost & Found Items', response.data)
        
        # Test keyword filter
        response_filter = self.client.get('/items?q=Dell&type=all')
        self.assertEqual(response_filter.status_code, 200)
        self.assertIn(b'Dell', response_filter.data)
        print("✓ Page 7 (Search Items) passed.")

    # 8. Item Details & Matching
    def test_08_item_details_and_matching(self):
        database = db.get_db()
        item = database.items.find_one({'title': {'$regex': 'Dell XPS 15 9520', '$options': 'i'}})
        self.assertIsNotNone(item)
        item_id = str(item['_id'])
        
        response = self.client.get(f'/item/{item_id}')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Dell XPS 15', response.data)
        self.assertIn(b'Smart Match Suggestions', response.data)
        
        # Check API endpoint for matches
        api_resp = self.client.get(f'/api/matches/{item_id}')
        self.assertEqual(api_resp.status_code, 200)
        json_data = api_resp.get_json()
        self.assertTrue(json_data['success'])
        self.assertGreater(len(json_data['matches']), 0)
        print(f"✓ Page 8 (Item Details & Smart Match with score {json_data['matches'][0]['match_score']}%) passed.")

    # 9. My Reports
    def test_09_my_reports(self):
        with self.client:
            self.client.post('/login', data={'email': 'rahul@lostlink.com', 'password': 'user123'})
            response = self.client.get('/my-reports')
            self.assertEqual(response.status_code, 200)
            self.assertIn(b'My Item Reports', response.data)
            self.assertIn(b'My Lost Items', response.data)
            print("✓ Page 9 (My Reports) passed.")

    # 10. Claim Requests
    def test_10_claim_requests(self):
        with self.client:
            self.client.post('/login', data={'email': 'rahul@lostlink.com', 'password': 'user123'})
            response = self.client.get('/claims')
            self.assertEqual(response.status_code, 200)
            self.assertIn(b'Claim Management', response.data)
            self.assertIn(b'Claims I Submitted', response.data)
            print("✓ Page 10 (Claim Requests) passed.")

    # 11. User Profile
    def test_11_user_profile(self):
        with self.client:
            self.client.post('/login', data={'email': 'rahul@lostlink.com', 'password': 'user123'})
            response = self.client.get('/profile')
            self.assertEqual(response.status_code, 200)
            self.assertIn(b'User Profile & Settings', response.data)
            self.assertIn(b'Personal Information', response.data)
            print("✓ Page 11 (User Profile) passed.")

    # 12. Admin Dashboard
    def test_12_admin_dashboard(self):
        with self.client:
            self.client.post('/login', data={'email': 'admin@lostlink.com', 'password': 'admin123'})
            response = self.client.get('/admin')
            self.assertEqual(response.status_code, 200)
            self.assertIn(b'Platform Administration', response.data)
            self.assertIn(b'Claims Moderation Queue', response.data)
            self.assertIn(b'Items Registry', response.data)
            self.assertIn(b'User Management', response.data)
            print("✓ Page 12 (Admin Dashboard) passed.")

    # 13. Printable Notice Flyer (Bonus MCA feature)
    def test_13_printable_flyer(self):
        database = db.get_db()
        item = database.items.find_one()
        item_id = str(item['_id'])
        response = self.client.get(f'/item/{item_id}/flyer')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'NOTICE FLYER', response.data)
        print("✓ Bonus Page (Printable Notice Poster) passed.")

if __name__ == '__main__':
    unittest.main()
