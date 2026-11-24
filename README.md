# LOSTLINK
## Smart Lost & Found Platform
> **Tagline: Lost Something? Let's Find It.**

An enterprise-grade, modern Web Application engineered for campus and community item recovery. Designed and developed as a Master of Computer Applications (MCA) Mini-Project.

---

## 📑 Table of Contents
1. [Project Overview](#project-overview)
2. [Technology Stack](#technology-stack)
3. [System Architecture](#system-architecture)
4. [Smart Matching Algorithm](#smart-matching-algorithm)
5. [Complete Pages Directory](#complete-pages-directory)
6. [Key Features](#key-features)
7. [Installation & Setup](#installation--setup)
8. [Connecting to MongoDB Atlas](#connecting-to-mongodb-atlas)
9. [Pre-configured Demo Accounts](#pre-configured-demo-accounts)
10. [MCA Viva Voce Q&A Preparation](#mca-viva-voce-qa-preparation)

---

## 1. Project Overview

On busy university campuses, offices, and institutions, hundreds of valuable personal belongings (laptops, wallets, identity cards, keys, smartphones) are misplaced daily. Traditional lost-and-found methods rely on manual notice boards, WhatsApp groups, or security offices, which suffer from poor visibility, privacy risks, and lack of verified ownership.

**LOSTLINK** solves this by providing:
- A centralized, real-time registry of **Lost** and **Found** property.
- An intelligent **Smart Matching Algorithm** that scores category, textual description, location landmarks, and dates.
- A secure **Claim Verification Workflow** where claimants must describe confidential marks or attach proof before physical handover.
- A dedicated **Admin Moderation Portal** with interactive analytics, audit logs, and resolution management.

---

## 2. Technology Stack

LOSTLINK strictly adheres to the mandated technical specifications:

| Component | Technology | Description |
| :--- | :--- | :--- |
| **Frontend** | HTML5, CSS3, JavaScript | Modern SaaS UI, Flexbox/Grid, Responsive, FontAwesome 6, Chart.js |
| **Backend** | Python Flask (v3.0+) | Lightweight WSGI web framework, REST routing, Jinja2 templating |
| **Database** | MongoDB | Document-oriented NoSQL database |
| **Driver** | PyMongo (v4.6+) | Official Python driver for MongoDB |
| **Database Hosting**| MongoDB Atlas | Cloud-native multi-cloud database service (with embedded viva fallback) |
| **IDE** | Google Antigravity | AI-native software engineering environment |

*No React, PHP, MySQL, or other database systems are used.*

---

## 3. System Architecture

```mermaid
flowchart TD
    subgraph Client["Client Browser (HTML5 / CSS3 / Vanilla JS)"]
        UI["Modern SaaS UI (Dark Navy / Indigo / Orange)"]
        SearchEngine["Live Debounced Search & Filter"]
        Charts["Chart.js Analytics Canvas"]
    end

    subgraph Server["Flask Application Server (Python 3.12)"]
        App["app.py (Controller & Routing)"]
        Auth["auth_service.py (Hash & Session RBAC)"]
        Matcher["matcher.py (Smart Matching Engine)"]
        Stats["stats_service.py (Analytics & Audit Logs)"]
    end

    subgraph DataLayer["Database & Storage Layer"]
        DBManager["db.py (Fail-Safe Database Layer)"]
        Atlas[("MongoDB Atlas Cloud Database")]
        EmbeddedStore[("Embedded Demo Engine (Offline Fallback)")]
        Uploads[("Static Media / Proof Uploads")]
    end

    UI -->|HTTP / Form / AJAX| App
    App --> Auth
    App --> Matcher
    App --> Stats
    App --> DBManager
    DBManager -->|PyMongo Driver| Atlas
    DBManager -.->|Fail-Safe Mode| EmbeddedStore
    App --> Uploads
```

---

## 4. Smart Matching Algorithm

One of the standout MCA academic features in LOSTLINK is the **Smart Matching Engine** (`services/matcher.py`). When a Lost item is viewed or created, the system compares it against active Found items (and vice-versa) using a multi-parameter scoring formula:

$$\text{Match Score} = S_{\text{category}} + S_{\text{text}} + S_{\text{location}} + S_{\text{date}}$$

### Scoring Breakdown:
1. **Category Compatibility ($S_{\text{category}}$, Max 35 Points):**
   - Exact category ID match = $35\text{ pts}$.
   - Complete mismatch = Terminated ($0\%$).

2. **Textual & Keyword Similarity ($S_{\text{text}}$, Max 35 Points):**
   - Computes normalized Jaccard similarity across filtered tokens:
     $$J(A, B) = \frac{|A \cap B|}{|A \cup B|}$$
   - Exact brand match bonus: $+5\text{ pts}$.
   - Exact color match bonus: $+5\text{ pts}$.
   - Title keyword overlap bonus: $+5\text{ pts}$.

3. **Location Proximity ($S_{\text{location}}$, Max 20 Points):**
   - Matches campus buildings, floor numbers, and landmarks (e.g., "Library 2nd Floor" vs. "Library Study Desk"): up to $20\text{ pts}$.

4. **Temporal Plausibility ($S_{\text{date}}$, Max 10 Points):**
   - If found within $0 \le \Delta t \le 14\text{ days}$ after loss: $10\text{ pts}$.
   - If found between $15 \le \Delta t \le 45\text{ days}$: $7\text{ pts}$.

The composite score ($0 - 100\%$) is classified as:
- **$\ge 75\%$:** High Match (Triggers priority dashboard alerts)
- **$50 - 74\%$:** Moderate Match
- **$35 - 49\%$:** Possible Lead

---

## 5. Complete Pages Directory

All 12 required pages have been implemented with consistent SaaS visual styling:

1. **Home Page (`/`)**: Hero banner, live recovery stats, 3-step workflow, recent item cards, category grid, CTA.
2. **User Registration (`/register`)**: Name, email, phone, campus department, password confirmation, validation.
3. **User Login (`/login`)**: Email, password, **1-Click Viva Demo credentials filler** for rapid evaluation.
4. **User Dashboard (`/dashboard`)**: Metric cards, Smart AI Match Alert widgets, my active reports, live activity feed.
5. **Report Lost Item (`/report-lost`)**: Title, category, brand, color, date lost, location landmark, unique marks, optional reward, photo upload.
6. **Report Found Item (`/report-found`)**: Title, category, brand, date found, location, custody/storage holding location, image upload.
7. **Search Items (`/items`)**: Keyword search, type toggle (All/Lost/Found), category filter, location filter, Grid and Table view toggle.
8. **Item Details (`/item/<id>`)**: High-res photograph, specifications, reporter info, Smart Match counterpart list, Claim modal trigger, public Q&A thread.
9. **My Reports (`/my-reports`)**: Tabbed interface for "My Lost Items" and "My Found Items", status indicators, Edit, Delete, and Mark Recovered actions.
10. **Claim Requests (`/claims`)**: Incoming claims on items I found & claims I submitted, with attached proof inspector and Approve/Reject controls.
11. **User Profile (`/profile`)**: Member info, campus affiliation, profile update, password change.
12. **Admin Dashboard (`/admin`)**: Platform overview, Chart.js category distribution and recovery rate donut chart, claims moderation queue, items registry, user role toggling.
13. **Printable Flyer (`/item/<id>/flyer`)**: *Bonus feature* — generates an A4 formatted printable missing/found notice flyer with one click!

---

## 6. Key Features

- **Role-Based Access Control (RBAC):** Users and Admins have distinct capabilities enforced by `@login_required` and `@admin_required` decorators.
- **Secure Password Hashing:** Uses PBKDF2 with SHA-256 via `werkzeug.security`.
- **Image Upload Management:** Validated file extensions (`.png`, `.jpg`, `.jpeg`, `.webp`), secure sanitized filenames, 16MB file size ceiling.
- **Privacy Shield:** Found item reports encourage keeping serial numbers secret; claimants must supply matching proof to prevent false claims.
- **Real-Time Interactive Search:** Instant debounced client-side filtering + full-text server-side MongoDB regex queries.
- **Fail-Safe Offline Mode:** If MongoDB Atlas is offline or internet is unavailable during college viva, the system gracefully continues running via the embedded JSON engine without throwing an unhandled exception.

---

## 7. Installation & Setup

### Prerequisites
- Python 3.10+ installed.

### Step 1: Clone or Navigate to Directory
```powershell
cd c:\LOSTLINK
```

### Step 2: Install Dependencies
```powershell
python -m pip install -r requirements.txt
```

### Step 3: Seed the Database
Populate the database with realistic sample items, users, claims, and matching pairs:
```powershell
python seed_data.py
```

### Step 4: Run the Application
```powershell
python app.py
```
Open your browser and navigate to:
```
http://127.0.0.1:5000
```

### Step 5: Run Automated Tests
```powershell
python test_app.py
```

---

## 8. Connecting to MongoDB Atlas

To connect LOSTLINK to your cloud MongoDB Atlas cluster:

1. Create a free cluster at [cloud.mongodb.com](https://cloud.mongodb.com).
2. Under **Security -> Database Access**, create a user (e.g., `lostlink_admin`).
3. Under **Security -> Network Access**, allow IP `0.0.0.0/0` (Allow from anywhere) or your current IP.
4. Under **Database -> Connect -> Drivers**, select Python and copy your connection string:
   ```
   mongodb+srv://<username>:<password>@cluster0.xxxxx.mongodb.net/lostlink_db?retryWrites=true&w=majority
   ```
5. Open `.env` in the root folder and paste your connection string:
   ```ini
   MONGODB_URI=mongodb+srv://lostlink_admin:YourPassword@cluster0.xxxxx.mongodb.net/lostlink_db?retryWrites=true&w=majority
   DB_NAME=lostlink_db
   ```
6. Run `python seed_data.py` to seed directly into your Atlas cloud cluster!
7. When you start `python app.py`, the top header and admin dashboard will display:
   `🟢 MongoDB Atlas Connected`

*(Note: If no connection string is set, the application automatically runs in Embedded Viva Mode, ensuring zero crashes during viva presentations!)*

---

## 9. Pre-configured Demo Accounts

Use these pre-seeded accounts or the **1-Click buttons** on `/login`:

| Role | Email | Password | Description |
| :--- | :--- | :--- | :--- |
| **Admin** | `admin@lostlink.com` | `admin123` | Department HOD with full moderation and analytics |
| **Student (Reporter)** | `rahul@lostlink.com` | `user123` | MCA student with lost laptop and wallet reports |
| **Student (Finder)** | `priya@lostlink.com` | `user123` | CSE student who reported found wallet and iPhone |
| **Campus Security** | `security@lostlink.com` | `user123` | Security guard managing holding lockers and keys |

---

## 10. MCA Viva Voce Q&A Preparation

### Q1: Why did you choose MongoDB instead of a Relational Database like MySQL?
**Answer:**
Lost and found items have highly heterogeneous and evolving attributes. An electronic gadget has brand, model, and serial number; a wallet has contents and card types; an ID card has student roll numbers; keys have ring count. In relational databases (MySQL), accommodating varying item schemas requires either sparse tables with numerous NULL columns or complex Entity-Attribute-Value (EAV) models. MongoDB's BSON document model allows flexible, schema-free storage where each item document stores its specific attributes naturally.

### Q2: How does the Smart Matching Algorithm work?
**Answer:**
The matching engine implements multi-criteria decision scoring across four dimensions:
1. Category filter (hard prerequisite, 35%).
2. Textual token similarity using Jaccard Coefficient $J(A,B) = \frac{|A \cap B|}{|A \cup B|}$ with bonus scoring for matching brand and color tokens (35%).
3. Location similarity matching campus buildings and floor keywords (20%).
4. Temporal date plausibility scoring whether the found date logically follows the loss date within an active window (10%).
Items scoring $\ge 75\%$ trigger high-priority alerts on user dashboards.

### Q3: How do you prevent fraudulent item claims?
**Answer:**
We implement a two-step privacy shield:
1. When report finders register items, the system advises them not to reveal secret identifying marks (e.g. phone lockscreen wallpapers, internal pocket contents, or serial numbers).
2. Claimants must submit private proof describing these hidden details or upload supporting invoices/receipts.
3. The claim enters a "Pending" moderation state visible only to the finder and system admin, who must approve the claim before personal contact information and handover directions are released.

### Q4: How is password security implemented in Flask?
**Answer:**
Passwords are never stored in plain text. We utilize `werkzeug.security.generate_password_hash` which generates a cryptographically secure hash using PBKDF2 with SHA-256 and an automatic cryptographic salt. Password verification is performed using `check_password_hash`, defending against rainbow table and timing attacks.

### Q5: How does the application handle MongoDB Atlas network interruptions?
**Answer:**
In `db.py`, the `DatabaseManager` handles connection timeouts with a safe 3-second threshold. If cloud connectivity is blocked by campus firewall or network dropouts during evaluation, the system automatically activates the embedded JSON-compatible store with identical PyMongo collection interfaces (`find`, `insert_one`, `update_one`, `delete_one`, `count_documents`). This guarantees continuous uptime during project demonstrations.
